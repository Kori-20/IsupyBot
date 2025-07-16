# Install
On the directory where the repository is:
- open terminal 
- run **->** ``pip install -r requirements.txt``
- go to **->** https://discord.com/developers/applications 
  - **->** Create new application
  - **->** copy application ID to a notepad for later 
ex.: ``ID99``
  - go to **->** Settings **->** Bot **->** Reset Token
    - Copy Token to notepad for later **!!!DO NOT SHARE THE TOKEN!!!**

# Set the token
- open .env **->** replace ``yourtoken`` with the application token 

# Set the bot Configs
- open **config.txt** and set:
    - ``ip_address`` (the ip/domain_name of the server)
    - ``channel_id`` (the id of the discord text channel)
        - right click over the intented channel and **->** Copy Link ex.:https://discord.com/channels/server_id/channel_id
        - copy and past channel_id onto the config file
- set the status ``frequency_level``
- if needed change the port in case server is running on a port other then 25565

# Create the server invite link 
- set ``ID99`` to your copied id in ``client_id=`` -> https://discord.com/oauth2/authorize?client_id=ID99&permissions=75776&integration_type=0&scope=bot
    -   the ``permissions=75776`` contains the following:
- Send Messages (to .... be able to send the message)
- Manage Messages (to be able to edit it's own message and pin it)
- Read Message History (to be able to search for it's own previous messages)

# Remove exemples keywords
- rename ``exemple.env`` **->** ``.env``
- rename ``config.exemple.txt`` **->** ``config.txt`` 

# Initiate the bot
- run ``./isupy.py`` or ``python3 isupy.py``


# What does the bot do?
- the bot will send an embed and pin it on the asigned text channel, updating it every ``x`` seconds defined by the ``frequency_level``
- the embed will contain the status of the server as well as it's verssion ammount of users and the names of the users   

