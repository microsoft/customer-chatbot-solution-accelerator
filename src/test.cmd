@echo off
 
call autoflake .
call isort .
call flake8 .