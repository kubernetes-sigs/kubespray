#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Constants related to the LDAP auth method."""

DEFAULT_GROUP_FILTER = '(|(memberUid={{.Username}})(member={{.UserDN}})(uniqueMember={{.UserDN}}))'
