# Datapull Dagmeister

## DataPull DagMeister process

<!-- toc -->

- [General](#general)
- [Notification system](#notification-system)
- [DagMeister instructions](#dagmeister-instructions)

<!-- tocstop -->

## General

- The DagMeister rotates every 2 weeks
  - To see who is the DagMeister now refer to
    [DataPull_DagMeister gsheet](https://docs.google.com/spreadsheets/d/12OhDW4hzSLekorrri2WfRkV8h3JcnB8WQd1JEL_n0D8/edit)
  - Each rotation should be confirmed by a 'handshake' between the outgoing
    DagMeister and the new one in the related Slack channel
    `#notifs-preprod-datapull`
  - Transfer the assignee of
    [#8785](https://github.com/cryptokaizen/cmamp/issues/8785) to new DagMeister
- The DagMeister is responsible for:
  - Check the Slack channel for any failures from preprod DAGs.
  - Raising the issue on Github for that failure by debugging the root cause of
    the failure.
    - If the issue is already raised, comment the link of the failure in the
      issue citing same reason.
  - Tag team leader in the issue to confirm if the issue needs to be fixed with
    highest priority or not.
  - All the failures from region `tokyo` are of highest priority and needs to be
    resolved ASAP.

## Notification system

- `@CK_Airflow_bot` notifies the team about breaks via Slack channel
  `Kaizen Preprod Datapull Notifications`
- A notification contains:
  - DAG start timestamp
  - Link fo broken DAG

## DagMeister instructions

- You receive a break notification from `@CK_Airflow_bot`
- Have a look at the message
  - Do it right away, this is always your highest priority task
- Notify the team
  - If the break happened in `tokyo` region for `bid_ask` or `OHLCV` DAGs ping
    the channel by tagging the team leader.
  - Reply on the failure to notify you are already looking into this.
  - After the issue is raised reply back with the issue number.
    - There could be multiple failure due to the same reason so just reply with
      same issue number.

- File an Issue in GH to report the failing tests and the errors
  - Paste the URL of the failing run
    - Example: [#9110](https://github.com/cryptokaizen/cmamp/issues/9110)
  - Provide as much information as possible to give an understanding of the
    problem
  - Stack trace or part of it (if it's too large)
  - Paste the link of QA notebook if QA failed.

- Fixing the issue
  - If the bug is obvious and can be fixed easily. Fix it with highest priority.
  - If fixing will require debugging time, tag the team leader to ask for
    priority.
    - IMPORTANT: Disabling a DAG is not the first choice, it's a measure of last
      resort! and should oly be done after the approval from the team leader.

- When your time of the DAGMeister duties is over, confirm the rotation with the
  next responsible person in the related Slack chat.
