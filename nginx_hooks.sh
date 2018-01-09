#!/bin/bash
set -e
openresty -t
openresty -s reload