1.) How to run on virtual environment:
    if not created: python -m venv venv

    # For Windows (Command Prompt)
    <env_name>\Scripts\activate

    # For Mac/Linux (Bash/Zsh)
    source <env_name>/bin/activate

    # For Windows (PowerShell) - may require setting execution policy first
    <env_name>\Scripts\Activate.ps1

    flask run

2.) How to run after installing requirements:
    flask init-db 
    python seed_db_enhanced.py (to download a testable database)
    flask run

3.) to reset db and run in one line:
    rm instance/chirp.db && flask init-db && python3 seed_db_enhanced.py && flask run

4.) Testing:
    Users: Aditya, Kabir, Testuser, testuser 
    Passwords: password

TODO: Make profiles clickable in timeline and in following and follower list in profile 
