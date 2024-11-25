-- [params]
-- int :offset

SELECT posts.id,posts.user_id,raw,EXTRACT(EPOCH FROM posts.created_at) AS created_at,reads FROM posts
JOIN topics
ON posts.topic_id = topics.id
WHERE 
posts.created_at BETWEEN TIMESTAMP WITH TIME ZONE '2024-01-01 00:00:00 Asia/Shanghai' 
AND TIMESTAMP WITH TIME ZONE '2025-01-01 00:00:00 Asia/Shanghai'
AND posts.deleted_at is NULL
AND NOT posts.hidden
AND topics.archetype = 'regular'
AND topics.deleted_at is NULL
AND posts.post_type = 1
ORDER BY posts.created_at
OFFSET :offset