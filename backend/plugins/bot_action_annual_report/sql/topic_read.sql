-- [params]
-- int :user_id

SELECT topic_id,total_msecs_viewed FROM topic_users
WHERE topic_id IN (
    SELECT id FROM topics
    WHERE created_at BETWEEN TIMESTAMP WITH TIME ZONE '2024-01-01 00:00:00 Asia/Shanghai' 
    AND TIMESTAMP WITH TIME ZONE '2025-01-01 00:00:00 Asia/Shanghai'
    AND topics.deleted_at is NULL
    AND topics.archetype = 'regular'
    AND topics.visible = true
)
AND user_id = :user_id
ORDER BY total_msecs_viewed DESC
LIMIT 10