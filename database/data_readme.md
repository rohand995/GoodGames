# Database Setup

## Installation and Setup

On MacOS run:  
```brew install postgresql@15 ```  

Then run ```brew services start postgresql@15``` to be able to execute postgres commands.
Stop this service when you are done.

## Create a Database

CREATE ROLE main WITH LOGIN PASSWORD 'access123';
ALTER ROLE main CREATEDB;
psql postgres -U main

## Data Model
Run the sql code in ```Database_Def.sql```