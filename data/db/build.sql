CREATE TABLE IF NOT EXISTS war_guild (
    GuildID interger PRIMARY KEY,
    Prefix text DEFAULT "&^",
    Gimmick text
    GatewayMessage interger DEFAULT 0
);

CREATE TABLE IF NOT EXISTS channels (
    ChannelName text PRIMARY KEY,
    ChannelID interger,
    ChannelType text,
    ChannelUsage text DEFAULT 'original'
);

CREATE TABLE IF NOT EXISTS members (
    UserID interger PRIMARY KEY,
    GameRole text
);

CREATE TABLE IF NOT EXISTS roles (
    RoleName text PRIMARY KEY,
    RoleID interger
);