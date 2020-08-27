# Zendesk Gather example API client for user contribution stats

This is a simple utility built in Python that creates a CSV file containing stats for users in a Zendesk Gather community.

## Requirements

This tool requires Python 3.x and the [requests](https://pypi.org/project/requests/) library installed.

## Usage

This is a command line tool, and it simply prints the CSV out. Invoke it like this:

```
python main.py -d <subdomain> -u <username> -t <token> -o <output_file> --from=<from> --to=<to>
```

Where:

 * `<subdomain>` is your zendesk subdomain.
 * `<username>` is your username.
 * `<token>` is your API token.
 * `<output_file>` is the desired output filename.
 * `<from>` is a date filter 'from' date (inclusive) in `yyyy-mm-dd` format.
 * `<to>` is a date filter 'to' date (inclusive) in `yyyy-mm-dd` format.
