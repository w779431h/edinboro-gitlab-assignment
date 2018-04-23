#!/usr/bin/env python3

# This module handle converting to email from student ID, and vice-versa

# convert student ID to email

def get_student_email(student_id):
    return "%s@scots.edinboro.edu" % student_id

def get_student_id(student_email):
    # splice off "@scots.edinboro.edu" to get id
    return student_email[:-len("@scots.edinboro.edu")]
