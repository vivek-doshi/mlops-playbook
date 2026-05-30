"""
Purpose:
    PPO (Proximal Policy Optimisation) trainer for RLHF.  Fine-tunes a policy
    model using feedback from a pre-trained reward model.  Uses the TRL library's
    PPOTrainer and logs all RLHF training metrics to MLflow under the experiment
    <model_name>-llm-ppo.

Usage:
    python llmops/rlhf/ppo_trainer.py \\
        --model-name       <name> \\
        --policy-model     <hf-model-id-or-adapter-path> \\
        --reward-model-uri <mlflow-artifacts-uri-or-local-path> \\
        --dataset-path     <dataset> \\
        --num-steps        1000

Dependencies:
    transformers>=4.40
    trl>=0.8
    torch>=2.2
    datasets>=2.18
    mlflow>=2.11
    accelerate>=0.28
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

try:
    import mlflow
    import torch
    from datasets import load_dataset
    from transformers import AutoModelForCausalLM, AutoModelForSequenceClassification, AutoTokenizer
    from trl import AutoModelForCausalLMWithValueHead, PPOConfig, PPOTrainer
except ImportError as exc:
    print(
        f"ERROR: {exc}\n"
        "Install with: pip install transformers trl torch datasets mlflow accelerate",
        file=sys.stderr,
    )
    sys.exit(1)


def run_ppo_training(
    model_name: str,
    policy_model_path: str,
    reward_model_path: str,
    dataset_path: str,
    num_steps: int = 1000,
    batch_size: int = 4,
    ppo_epochs: int = 4,
    learning_rate: float = 1.4e-5,
    output_dir: str = "outputs/ppo",
) -> None:
    """Fine-tune a policy model with PPO and log to MLflow."""
    experiment_name = f"{model_name}-llm-ppo"
    mlflow.set_experiment(experiment_name)

    with mlflow.start_run(
        tags={"llm_task": "ppo", "policy_model": policy_model_path}
    ) as run:
        mlflow.log_params(
            {
                "policy_model": policy_model_path,
                "reward_model": reward_model_path,
                "dataset": dataset_path,
                "num_steps": num_steps,
                "batch_size": batch_size,
                "ppo_epochs": ppo_epochs,
                "learning_rate": learning_rate,
            }
        )

        tokenizer = AutoTokenizer.from_pretrained(policy_model_path)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        policy_model = AutoModelForCausalLMWithValueHead.from_pretrained(policy_model_path)

        reward_tokenizer = AutoTokenizer.from_pretrained(reward_model_path)
        if reward_tokenizer.pad_token is None:
            reward_tokenizer.pad_token = reward_tokenizer.eos_token
        reward_model = AutoModelForSequenceClassification.from_pretrained(reward_model_path)
        reward_model.eval()

        ppo_config = PPOConfig(
            model_name=model_name,
            learning_rate=learning_rate,
            batch_size=batch_size,
            ppo_epochs=ppo_epochs,
            log_with="tensorboard",
        )

        dataset = load_dataset(dataset_path, split="train")
        prompts = [ex["prompt"] for ex in dataset][:num_steps]

        ppo_trainer = PPOTrainer(
            config=ppo_config,
            model=policy_model,
            tokenizer=tokenizer,
        )

        start_time = time.time()
        for step, prompt in enumerate(prompts):
            query_tensors = tokenizer.encode(prompt, return_tensors="pt")[0].to(
                ppo_trainer.accelerator.device
            )

            response_tensors = ppo_trainer.generate(
                query_tensors.unsqueeze(0),
                max_new_tokens=128,
                do_sample=True,
                temperature=0.7,
            ).squeeze(0)

            response_text = tokenizer.decode(response_tensors, skip_special_tokens=True)

            # Score with reward model
            reward_inputs = reward_tokenizer(
                prompt + response_text,
                return_tensors="pt",
                truncation=True,
                max_length=512,
            ).to(reward_model.device)
            with torch.no_grad():
                rewards = reward_model(**reward_inputs).logits.squeeze(-1)

            stats = ppo_trainer.step(
                [query_tensors],
                [response_tensors],
                [rewards],
            )

            if step % 50 == 0:
                mlflow.log_metrics(
                    {
                        "mean_reward": float(rewards.mean().item()),
                        "ppo_loss": float(stats.get("ppo/loss/total", 0.0)),
                        "kl_divergence": float(stats.get("objective/kl", 0.0)),
                    },
                    step=step,
                )

        # Save fine-tuned policy
        model_dir = Path(output_dir) / run.info.run_id
        model_dir.mkdir(parents=True, exist_ok=True)
        ppo_trainer.save_model(str(model_dir))
        tokenizer.save_pretrained(str(model_dir))

        mlflow.log_artifacts(str(model_dir), artifact_path="ppo_model")
        mlflow.log_metric("training_wall_seconds", time.time() - start_time)

        print(f"✓ PPO training complete. Run ID: {run.info.run_id}")


def _parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Run RLHF PPO fine-tuning.")
    parser.add_argument("--model-name", required=True)
    parser.add_argument("--policy-model", required=True, dest="policy_model_path")
    parser.add_argument("--reward-model-uri", required=True, dest="reward_model_path")
    parser.add_argument("--dataset-path", required=True)
    parser.add_argument("--num-steps", type=int, default=1000)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--ppo-epochs", type=int, default=4)
    parser.add_argument("--learning-rate", type=float, default=1.4e-5)
    parser.add_argument("--output-dir", default="outputs/ppo")
    return parser.parse_args(argv)


def main(argv=None):
    args = _parse_args(argv)
    run_ppo_training(
        model_name=args.model_name,
        policy_model_path=args.policy_model_path,
        reward_model_path=args.reward_model_path,
        dataset_path=args.dataset_path,
        num_steps=args.num_steps,
        batch_size=args.batch_size,
        ppo_epochs=args.ppo_epochs,
        learning_rate=args.learning_rate,
        output_dir=args.output_dir,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
