# allukabot // @zoldycktmbot 
> with HunterxHunter theme.


[![Open Source Love](https://badges.frapsoft.com/os/v1/open-source.png?v=103)](https://github.com/ellerbrock/open-source-badges/)  
[![GPLv3 license](https://img.shields.io/badge/License-GPLv3-blue.svg)](http://perso.crans.org/besson/LICENSE.html)

Modular Telegram bot for managing your groups with a extras features with HunterxHunter theme.

[![alluka](https://telegra.ph/file/4d3a649980e88c3eeb362.jpg)](https://telegram.dog/zoldycktmbot)

### Configuration

Rename `sample_config.yml` to `config.yml` 

`alluka_explain_config: "hunter_____X_____hunter"` replace this line `hunter_____X_____hunter` with this `alluka_zoldyck`


The following env variables are supported:

 - `bot_token`: Your bot token, as a string.
 - `owner_id`: An integer of consisting of your owner ID
 - `owner_username`: Your username

 - `database_urlL`: Your database URL
 - `message_dump`: optional: a chat where your replied saved messages are stored, to stop people deleting their old 
 - `load`: Space separated list of modules you would like to load
 - `no_load`: Space separated list of modules you would like NOT to load
 - `webhook`: Setting this to ANYTHING will enable webhooks when in env mode
 messages
 - `url`: The URL your webhook should connect to (only needed for webhook mode)

 - `sudo_users`: A space separated list of user_ids which should be considered sudo users
 - `whitelist_users`: A space separated list of user_ids which should be considered support users (can gban/ungban,
 nothing else)
 - `support_users`: A space separated list of user_ids, they can be banned.
 - `cert_path`: Path to your webhook certifdev_usersicate
 - `port`: Port to use for your webhooks
 - `del_cmds`: Whether to delete commands from users which don't have rights to use that command
 - `strict_gban`: Enforce gbans across new groups as well as old groups. When a gbanned user talks, he will be banned.
 - `strict_gmute`: Enforce gbans across new groups as well as old groups. When a gbanned user talks, he will be banned.
 - `workers`: Number of threads to use. 8 is the recommended (and default) amount, but your experience may vary.
 __Note__ that going crazy with more threads wont necessarily speed up your bot, given the large amount of sql data 
 accesses, and the way python asynchronous calls work.
 - `ban_sticker`: Which sticker to use when banning people.
 - `allow_excl`: Whether to allow using exclamation marks ! for commands as well as /.

### Python dependencies

Install the necessary python dependencies by moving to the project directory and running:

`pip3 install -r requirements.txt`.

This will install all necessary python packages.

### Database

If you wish to use a database-dependent module (eg: locks, notes, userinfo, users, filters, welcomes),
you'll need to have a database installed on your system. I use postgres, so I recommend using it for optimal compatibility.

In the case of postgres, this is how you would set up a the database on a debian/ubuntu system. Other distributions may vary.

- install postgresql:

`sudo apt-get update && sudo apt-get install postgresql`

- change to the postgres user:

`sudo su - postgres`

- create a new database user (change YOUR_USER appropriately):

`createuser -P -s -e YOUR_USER`

This will be followed by you needing to input your password.

- create a new database table:

`createdb -O YOUR_USER YOUR_DB_NAME`

Change YOUR_USER and YOUR_DB_NAME appropriately.

- finally:

`psql YOUR_DB_NAME -h YOUR_HOST YOUR_USER`

This will allow you to connect to your database via your terminal.
By default, YOUR_HOST should be 0.0.0.0:5432.

You should now be able to build your database URI. This will be:

`sqldbtype://username:pw@hostname:port/db_name`

Replace sqldbtype with whichever db youre using (eg postgres, mysql, sqllite, etc)
repeat for your username, password, hostname (localhost?), port (5432?), and db name.


