-- [params]
-- int :user_id

SELECT tags.name,count(posts.id)
FROM tags
JOIN topic_tags
ON tags.id = topic_tags.tag_id
JOIN topics
ON topics.id = topic_tags.topic_id
JOIN posts
ON posts.topic_id = topics.id
WHERE posts.created_at BETWEEN TIMESTAMP WITH TIME ZONE '2024-01-01 00:00:00 Asia/Shanghai' 
AND TIMESTAMP WITH TIME ZONE '2025-01-01 00:00:00 Asia/Shanghai'
AND posts.user_id = :user_id
AND posts.deleted_at is NULL
AND NOT posts.hidden
AND topics.archetype = 'regular'
AND topics.deleted_at is NULL
AND tags.id NOT IN(
    SELECT tag_id
    FROM tag_group_memberships
    WHERE tag_group_id IN (11,1)
)
AND tags.name NOT IN ('涉政','发发牢骚')
GROUP BY tags.id
ORDER BY count(posts.id) DESC
LIMIT 10