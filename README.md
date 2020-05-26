# Zendesk Gather example API client for user contribution stats

This is a simple utility built in Python that creates a CSV file containing stats for users in a Zendesk Gather community.

## Usage

This is a command line tool, and it simply prints the CSV out. Invoke it like this:

```
python main.py -d <subdomain> -u <username> -t <token>
```

Where:

 * `≤subdomain>` is your zendesk subdomain.
 * `<username>` is your username
 * `<token>` is your API token
