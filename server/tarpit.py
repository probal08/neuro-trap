"""
Module 17: Data Exhaustion Tar Pit
Cyber Immune System — Fever Response Layer

When an attacker tries to exfiltrate data (mysqldump, pg_dump, etc.),
this module traps them in an infinite loop of AI-generated fake data,
exhausting their scraping bot's memory until it crashes.
"""
import random
import string
import time

# Fake data generators
FIRST_NAMES = ["James", "Maria", "Robert", "Jennifer", "David", "Linda", "William",
               "Patricia", "Richard", "Elizabeth", "Joseph", "Barbara", "Thomas", "Susan",
               "Michael", "Sarah", "Daniel", "Karen", "Matthew", "Nancy", "Ahmed", "Chen",
               "Raj", "Yuki", "Olga", "Pierre", "Hans", "Diego", "Anastasia", "Wei"]

LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
              "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson",
              "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Kumar", "Li",
              "Park", "Tanaka", "Ivanov", "Muller", "Rossi", "Santos", "Kim", "Nguyen"]

DOMAINS = ["gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "company.com",
           "corporate.net", "enterprise.org", "mail.ru", "protonmail.com", "icloud.com"]

CITIES = ["New York", "London", "Tokyo", "Mumbai", "Berlin", "Sydney", "Toronto",
          "Singapore", "Dubai", "São Paulo", "Moscow", "Seoul", "Paris", "Lagos"]

def _random_email(first, last):
    domain = random.choice(DOMAINS)
    return f"{first.lower()}.{last.lower()}{random.randint(1,99)}@{domain}"

def _random_phone():
    return f"+{random.randint(1,91)}-{random.randint(100,999)}-{random.randint(100,999)}-{random.randint(1000,9999)}"

def _random_cc():
    """Generate a fake (invalid) credit card number."""
    return f"{random.randint(4000,4999)}-{random.randint(1000,9999)}-{random.randint(1000,9999)}-{random.randint(1000,9999)}"

def _random_ssn():
    return f"{random.randint(100,999)}-{random.randint(10,99)}-{random.randint(1000,9999)}"

def _random_ip():
    return f"{random.randint(1,223)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"

def _random_password():
    chars = string.ascii_letters + string.digits + "!@#$%"
    return ''.join(random.choices(chars, k=random.randint(8, 16)))


def generate_fake_sql_rows(count=50):
    """Generate realistic-looking SQL table dump rows."""
    header = "+---------+----------------------+---------------------------+-------------------+---------------------+"
    columns = "| user_id | full_name            | email                     | phone             | created_at          |"
    
    lines = [header, columns, header]
    
    for i in range(count):
        uid = random.randint(1000, 99999)
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        name = f"{first} {last}"
        email = _random_email(first, last)
        phone = _random_phone()
        year = random.randint(2020, 2026)
        month = random.randint(1, 12)
        day = random.randint(1, 28)
        created = f"{year}-{month:02d}-{day:02d} {random.randint(0,23):02d}:{random.randint(0,59):02d}:{random.randint(0,59):02d}"
        
        lines.append(f"| {uid:<7} | {name:<20} | {email:<25} | {phone:<17} | {created} |")
    
    lines.append(header)
    lines.append(f"{count} rows in set (0.{random.randint(10,99)} sec)")
    return "\n".join(lines)


def generate_fake_csv_dump(count=50):
    """Generate realistic CSV data dump."""
    lines = ["id,name,email,ssn,credit_card,balance,city,last_login"]
    
    for i in range(count):
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        lines.append(
            f"{random.randint(1,99999)},{first} {last},"
            f"{_random_email(first, last)},{_random_ssn()},"
            f"{_random_cc()},{random.randint(100,999999)}.{random.randint(10,99)},"
            f"{random.choice(CITIES)},{random.randint(2024,2026)}-{random.randint(1,12):02d}-{random.randint(1,28):02d}"
        )
    return "\n".join(lines)


def generate_fake_passwd():
    """Generate a realistic /etc/passwd dump with many users."""
    lines = [
        "root:x:0:0:root:/root:/bin/bash",
        "daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin",
        "bin:x:2:2:bin:/bin:/usr/sbin/nologin",
        "sys:x:3:3:sys:/dev:/usr/sbin/nologin",
        "www-data:x:33:33:www-data:/var/www:/usr/sbin/nologin",
        "mysql:x:27:27:MySQL Server:/var/lib/mysql:/bin/false",
        "sshd:x:74:74:Privilege-separated SSH:/var/empty/sshd:/sbin/nologin",
    ]
    for i in range(20):
        first = random.choice(FIRST_NAMES).lower()
        uid = 1000 + i
        lines.append(f"{first}:x:{uid}:{uid}:{first.title()} User:/home/{first}:/bin/bash")
    return "\n".join(lines)


def activate_tarpit(command, channel=None):
    """
    Main tarpit function. Detects exfiltration attempts and
    feeds infinite fake data at deliberately slow speed.
    
    Returns the fake data string if no channel (for testing),
    or streams it directly to the channel.
    """
    cmd_lower = command.lower()
    
    # Module 31: Archive of Death (Zip Bomb)
    if 'tar ' in cmd_lower or 'zip ' in cmd_lower:
        if channel:
            channel.send("Compressing filesystem... please wait (Archive of Death Active)\r\n")
            try:
                # Blast the attacker's terminal/client with highly compressive repeating bytes 
                # that consume massive RAM when processed.
                chunk = "A" * 1024 * 1024
                while True:
                    channel.send(chunk)
            except:
                return ""  # Stopped
        return "Archive of Death triggered."

    # Module 32: Network Black Hole (Protocol Tarpit)
    elif 'nc ' in cmd_lower or 'wget ' in cmd_lower or 'curl ' in cmd_lower:
        if channel:
            channel.send("Connecting to remote host... (Network Black Hole Active)\r\n")
            try:
                # Send 1 byte per second, infinitely freezing the attacker's bot.
                while True:
                    channel.send(random.choice(string.ascii_letters))
                    time.sleep(1)
            except:
                return ""  # Stopped
        return "Network Black Hole triggered."
        
    # Standard DB Exhaustion Tarpit
    elif any(x in cmd_lower for x in ['mysqldump', 'pg_dump', 'mongodump']):
        fake_data = generate_fake_sql_rows(100)
        prefix = f"-- MySQL dump 10.13  Distrib 8.0.28\n-- Host: localhost    Database: production_db\n-- Server version 8.0.28\n\n"
        return prefix + fake_data
    
    elif 'cat /etc/shadow' in cmd_lower:
        lines = []
        for i in range(15):
            name = random.choice(FIRST_NAMES).lower()
            salt = ''.join(random.choices(string.ascii_letters, k=8))
            hash_val = ''.join(random.choices(string.ascii_letters + string.digits, k=43))
            lines.append(f"{name}:$6${salt}${hash_val}:19000:0:99999:7:::")
        return "\n".join(lines)
    
    elif any(x in cmd_lower for x in ['select *', 'select ', 'dump']):
        return generate_fake_sql_rows(50)
    
    else:
        return generate_fake_csv_dump(30)
