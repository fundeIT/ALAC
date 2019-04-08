#!/bin/sh

mongoexport --db alac --collection clients --type csv --fields age,sex,vulnerable,rol,city
