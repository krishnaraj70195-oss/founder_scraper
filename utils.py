import csv
import os


RESULTS_FILE = "output/results.csv"
FAILED_FILE = "output/failed.csv"


def load_websites(path):

    with open(path, "r") as f:

        websites = [
            line.strip()
            for line in f.readlines()
            if line.strip()
        ]

    return list(dict.fromkeys(websites))


def create_output_files():

    if not os.path.exists(RESULTS_FILE):

        with open(RESULTS_FILE, "w", newline="") as f:

            writer = csv.writer(f)

            writer.writerow([
                "website",
                "role",
                "full_name"
            ])

    if not os.path.exists(FAILED_FILE):

        with open(FAILED_FILE, "w", newline="") as f:

            writer = csv.writer(f)

            writer.writerow([
                "website"
            ])


def append_result(website, role, full_name):

    with open(RESULTS_FILE, "a", newline="") as f:

        writer = csv.writer(f)

        writer.writerow([
            website,
            role,
            full_name
        ])


def append_failed(website):

    with open(FAILED_FILE, "a", newline="") as f:

        writer = csv.writer(f)

        writer.writerow([
            website
        ])


def load_completed_websites():

    completed = set()

    if not os.path.exists(RESULTS_FILE):
        return completed

    with open(RESULTS_FILE, "r") as f:

        reader = csv.DictReader(f)

        for row in reader:
            completed.add(row["website"])

    return completed
