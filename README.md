# calcifer

A Python tool to fetch the main contributors of all repos within an org.

How to
> poetry run calcifer --github-org <orgname> --out-file-path <path to output>
  
The output is a CSV file with the top n contributors from the same org, with n defaulted to 3 or set via --n-contrib.
