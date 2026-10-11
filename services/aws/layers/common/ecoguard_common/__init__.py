"""Shared code for every EcoGuard Lambda.

Pure helpers (tags, urls, responses) import nothing from AWS so they can be unit tested locally.
AWS-touching modules (db, storage, notify) import boto3 lazily.
"""
