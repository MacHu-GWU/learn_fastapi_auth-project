# -*- coding: utf-8 -*-

from esc_tpl_lbd.one.api import one

answer = input(
    "Are you sure to delete all the deployed resources? "
    "Enter 'Y' to continue: "
)
if answer.strip().upper() == "Y":
    one.delete_config()
else:
    print("Aborted")
