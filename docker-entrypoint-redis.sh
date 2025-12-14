#!/bin/sh
# Redis entrypoint script to handle password with special characters

# Create redis.conf with password properly quoted
# Using printf to safely handle special characters
cat > /tmp/redis.conf << 'EOF'
# Redis Configuration
appendonly yes
bind 0.0.0.0
protected-mode no
appendfilename "appendonly.aof"
appendfsync everysec
EOF

# Add requirepass with properly quoted password
printf 'requirepass "%s"\n' "$REDIS_PASSWORD" >> /tmp/redis.conf

# Start Redis with the generated config
exec redis-server /tmp/redis.conf
