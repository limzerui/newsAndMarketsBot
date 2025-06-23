#!/usr/bin/env python3
"""
Subscriber Manager

A utility script to check and manage subscribers to the Financial News Bot.
"""

import json
import os
import argparse
from datetime import datetime

SUBSCRIBERS_FILE = 'subscribers.json'

def load_subscribers():
    """Load subscribers from file."""
    try:
        if os.path.exists(SUBSCRIBERS_FILE):
            with open(SUBSCRIBERS_FILE, 'r') as f:
                return json.load(f)
        return {}
    except Exception as e:
        print(f"Error loading subscribers: {str(e)}")
        return {}

def save_subscribers(subscribers):
    """Save subscribers to file."""
    try:
        with open(SUBSCRIBERS_FILE, 'w') as f:
            json.dump(subscribers, f, indent=2)
        print(f"Successfully saved {len(subscribers)} subscribers to {SUBSCRIBERS_FILE}")
    except Exception as e:
        print(f"Error saving subscribers: {str(e)}")

def display_subscribers(subscribers=None):
    """Display all subscribers."""
    if subscribers is None:
        subscribers = load_subscribers()
    
    if not subscribers:
        print("No subscribers found.")
        return
    
    print(f"\n{'=' * 60}")
    print(f"{'ID':<15} | {'Username':<20} | {'Status':<10} | {'Subscribed At'}")
    print(f"{'-' * 60}")
    
    active_count = 0
    inactive_count = 0
    
    for user_id, data in subscribers.items():
        status = "Active" if data.get("active", True) else "Inactive"
        username = data.get("username", "N/A")
        subscribed_at = data.get("subscribed_at", "N/A")
        
        if data.get("active", True):
            active_count += 1
        else:
            inactive_count += 1
        
        print(f"{user_id:<15} | {username:<20} | {status:<10} | {subscribed_at}")
    
    print(f"{'=' * 60}")
    print(f"Total: {len(subscribers)} subscribers ({active_count} active, {inactive_count} inactive)")

def add_subscriber(user_id, username=None, first_name=None):
    """Add a new subscriber."""
    subscribers = load_subscribers()
    user_id = str(user_id)
    
    if user_id in subscribers and subscribers[user_id].get("active", True):
        print(f"User {user_id} is already an active subscriber.")
        return
    
    subscribers[user_id] = {
        "username": username if username else "N/A",
        "first_name": first_name if first_name else "N/A",
        "subscribed_at": datetime.now().isoformat(),
        "active": True
    }
    
    save_subscribers(subscribers)
    print(f"Added subscriber: {user_id}")

def remove_subscriber(user_id):
    """Remove a subscriber."""
    subscribers = load_subscribers()
    user_id = str(user_id)
    
    if user_id not in subscribers:
        print(f"User {user_id} is not a subscriber.")
        return
    
    if not subscribers[user_id].get("active", True):
        print(f"User {user_id} is already inactive.")
        return
    
    subscribers[user_id]["active"] = False
    subscribers[user_id]["unsubscribed_at"] = datetime.now().isoformat()
    
    save_subscribers(subscribers)
    print(f"Removed subscriber: {user_id}")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Subscriber Manager')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List all subscribers')
    
    # Add command
    add_parser = subparsers.add_parser('add', help='Add a new subscriber')
    add_parser.add_argument('user_id', type=str, help='Telegram user ID')
    add_parser.add_argument('--username', type=str, help='Telegram username (optional)')
    add_parser.add_argument('--first_name', type=str, help='User first name (optional)')
    
    # Remove command
    remove_parser = subparsers.add_parser('remove', help='Remove a subscriber')
    remove_parser.add_argument('user_id', type=str, help='Telegram user ID')
    
    args = parser.parse_args()
    
    if args.command == 'list':
        display_subscribers()
    elif args.command == 'add':
        add_subscriber(args.user_id, args.username, args.first_name)
    elif args.command == 'remove':
        remove_subscriber(args.user_id)
    else:
        display_subscribers()
        print("\nUse one of the following commands:")
        print("  python3 check_subscribers.py list")
        print("  python3 check_subscribers.py add <user_id> [--username USERNAME] [--first_name FIRST_NAME]")
        print("  python3 check_subscribers.py remove <user_id>")

if __name__ == "__main__":
    main() 