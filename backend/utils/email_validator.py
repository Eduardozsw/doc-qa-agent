_DISPOSABLE_DOMAINS = {
    "mailinator.com", "tempmail.com", "guerrillamail.com", "10minutemail.com",
    "throwam.com", "yopmail.com", "trashmail.com", "fakeinbox.com",
    "sharklasers.com", "guerrillamailblock.com", "grr.la", "guerrillamail.info",
    "guerrillamail.biz", "guerrillamail.de", "guerrillamail.net", "guerrillamail.org",
    "spam4.me", "dispostable.com", "maildrop.cc", "mailnull.com",
    "spamgourmet.com", "trashmail.at", "trashmail.io", "trashmail.me",
    "discard.email", "spamfree24.org", "notsharingmy.info", "filzmail.com",
    "throwam.com", "tempinbox.com", "spambox.us", "mailexpire.com",
    "spamevader.com", "jetable.fr.nf", "nwldx.com", "sharedmailbox.org",
}


def is_disposable_email(email: str) -> bool:
    domain = email.strip().lower().split("@")[-1] if "@" in email else ""
    return domain in _DISPOSABLE_DOMAINS
