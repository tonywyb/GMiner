#!/bin/bash
echo 'dataset = ' $1
echo 'min_sup = ' $2
echo 'min_conf = ' $3
python association_rule_mining.py $1 $2 $3 > example-run.txt