I have some long-running script `long_task` that outputs something to the stdout.
The output happens in birsts of lines, after a set of lines has been output 
the `long_task` freezes and waits for some time. This may be the output from 
`tail -f` command, or a script reacting on changes in Fit repositories.

Write bash script `report_task_log.sh`, according to the following requirements:

- It can be run from terminal or from other program (say, Telegram bot)
- The `long_task` had been started separately, independently of `report_task_log.sh`
- It fetches all the lines output by `long_task` since last run of the script and outputs
  to stdout

Make a plan first in MD format. Write code after review of the plan.
