#!/bin/bash

WORKDIR=/home/clawer/cr-crawler/clawer

DJANGO_SETTINGS_MODULE="clawer.settings_local" rqworker --url redis://10.0.1.3/0  -v -P ${WORKDIR} down_super down_high down_medium down_low