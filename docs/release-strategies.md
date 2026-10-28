# Model Release Strategies

## Canary

Use a canary when the model has meaningful live traffic and the serving platform
can route by percentage. Start with 1-10% traffic, compare error rate, latency,
drift, fairness, and business KPIs, then expand only after the observation window
passes.

## Blue/green

Use blue/green when a full parallel environment is affordable and instant rollback
is more important than gradual exposure. Keep the previous environment available
until the new model passes the observation window.

## Shadow

Use shadow traffic when predictions can be evaluated without affecting users.
The Triton shadow pattern in `serving/triton/shadow-deployment.yaml` is a reference
only; production use requires privacy review, load controls, and comparison of
quality and latency.

## Champion/challenger

Keep the current production model as champion and evaluate the challenger against
the same feature and label stream. Promotion requires a signed comparison report,
model-card update, and human approval.

## Automated rollback

Rollback must be triggered by an SLO breach, severe model-quality regression, or
failed health check. It must restore the previous immutable image and model
artifact, verify health, and record the incident and model version.
