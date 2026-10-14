### Database setup ###

- Tables:
  - users(login accounts)
    - columns:  
      - Id, email, passwordhash,fullname,role,isverified,verified_token,reset_token,expires,created_at
  - Customers:
    - columns:
      - cID,user 