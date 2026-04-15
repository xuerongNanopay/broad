---
name: sql-nba-finals
description: Retrieve stats from NBA finals, and format them into SQL insertion statement. 
---

# SQL NBA Finals
This skill acts as NBA information sourcer. It provides data from most recent 20 years of NBP Finals,
and format into SQL insertion statement. It should provides the table scheme as well.

## Instructions

1. **Retrieve stats from NBA finals in the model with using external tools.
2. **The infomation should include:
    - which year belong to 
    - which team won the final
    - which team lose the final
    - how many games did both teams play
    - who is the final MVP
    - which city held the last game
3. **Generate output meet belong requirements:
    - a SQL statement to create a table base on above requirement
    - insert statement of the most recent 20 years