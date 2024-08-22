import os
import praw
import config
import time
import requests
from bs4 import BeautifulSoup

number_of_entries = 25  # entries searched per run
pause = 5  # number of seconds in between runs
# link to gym occupancy data
url = "https://connect.recsports.vt.edu/facilityoccupancy"
high_occupancy = 500
low_occupancy = 250
empty = 5  # not 0 in case people forgot to sign out


def bot_login():
    print("Logging in...")
    reddit = praw.Reddit(username=config.username,
                         password=config.password,
                         client_id=config.client_id,
                         client_secret=config.client_secret,
                         user_agent="Gym occupancy comment responder 1.0 by /u/bigshark-")
    print("Logged in successfully!")
    return reddit


def get_occupancy():
    response = requests.get(url)  # Capturing info from request
    # Parsing HTML content using BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')

    # Finding canvas element with the data-occupancy attribute
    canvas = soup.find('canvas', {'class': 'occupancy-chart'})
    if canvas and 'data-occupancy' in canvas.attrs:
        occupancy = canvas['data-occupancy']
        return int(occupancy)
    else:
        raise ValueError("Occupancy data not found in the HTML content")


def run_bot(reddit, comments_replied_to):
    if not reddit:
        print("Reddit instance is not available. Exiting...")
        return

    occupancy = get_occupancy()
    print("Current occupancy:", occupancy)
    print("Searching through " + str(number_of_entries) + " comments...")

    for comment in reddit.subreddit('VirginiaTech').comments(limit=number_of_entries):
        if '!occupancy' in comment.body.lower() and comment.id not in comments_replied_to:
            print(f"A comment looking for a McComas' occupancy was found by: {comment.author}: {comment.body}")

            if occupancy > high_occupancy:
                reply_message = ("McComas is really busy right now with a current occupancy of " + str(occupancy) +
                                 ". I'd check back later to see if it dies down.")
            elif low_occupancy > occupancy > empty:
                reply_message = ("McComas is fairly unoccupied with a current occupancy of " + str(occupancy) +
                                 ". Now's would be a great time to go!")
            elif occupancy < empty:
                reply_message = ("McComas is empty right now. I would check"
                                 " https://recsports.vt.edu/facilities/hours.html to see if the gym is open.")
            else:
                reply_message = ("McComas is neither crowded nor empty with a current occupancy of " +
                                 str(occupancy) + ".")

            comment.reply(reply_message)
            print("Replied to comment " + comment.id)

            # add comment id to array and txt file
            comments_replied_to.append(comment.id)
            with open("replied_comments.txt", "a") as f:
                f.write(comment.id + "\n")

    print("sleeping for " + str(pause) + " seconds")
    time.sleep(pause)


def get_saved_comments():
    if not os.path.isfile("replied_comments.txt"):
        return []
    else:
        with open("replied_comments.txt", "r") as f:
            comments_replied_to = f.read().splitlines()
            return comments_replied_to


if __name__ == "__main__":
    replied_comments = get_saved_comments()
    while True:
        r = bot_login()
        run_bot(r, replied_comments)
