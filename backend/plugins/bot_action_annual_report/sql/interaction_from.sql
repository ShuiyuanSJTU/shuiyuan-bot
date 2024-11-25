-- [params]
-- int :target_user_id


WITH r AS (
    SELECT retorts.user_id as from_user_id, count(retorts.id) as count
    FROM retorts
    INNER JOIN posts
    ON retorts.post_id = posts.id
    INNER JOIN topics
    ON posts.topic_id = topics.id
    INNER JOIN categories
    ON categories.id = topics.category_id
    WHERE retorts.created_at BETWEEN TIMESTAMP WITH TIME ZONE '2024-01-01 00:00:00 Asia/Shanghai' 
    AND TIMESTAMP WITH TIME ZONE '2025-01-01 00:00:00 Asia/Shanghai'
    AND retorts.deleted_at is NULL
    AND posts.deleted_at is NULL
    AND posts.user_id = :target_user_id
    AND topics.archetype = 'regular'
    AND topics.deleted_at is NULL
    AND categories.read_restricted = False
    GROUP BY retorts.user_id
),
l AS (
    SELECT post_actions.user_id as from_user_id,count(post_actions.id) as count
    FROM post_actions
    INNER JOIN posts
    ON post_actions.post_id = posts.id
    INNER JOIN topics
    ON posts.topic_id = topics.id
    INNER JOIN categories
    ON categories.id = topics.category_id
    WHERE post_actions.created_at BETWEEN TIMESTAMP WITH TIME ZONE '2023-01-01 00:00:00 Asia/Shanghai' 
    AND TIMESTAMP WITH TIME ZONE '2024-01-01 00:00:00 Asia/Shanghai'
    AND post_actions.deleted_at is NULL
    AND posts.deleted_at is NULL
    AND posts.user_id = :target_user_id
    AND topics.archetype = 'regular'
    AND topics.deleted_at is NULL
    AND categories.read_restricted = False
    GROUP BY post_actions.user_id
),
p AS (
    SELECT posts.user_id as from_user_id,count(posts.id) as count
    FROM posts
    INNER JOIN topics
    ON posts.topic_id = topics.id
    INNER JOIN categories
    ON categories.id = topics.category_id
    WHERE posts.created_at BETWEEN TIMESTAMP WITH TIME ZONE '2023-01-01 00:00:00 Asia/Shanghai' 
    AND TIMESTAMP WITH TIME ZONE '2024-01-01 00:00:00 Asia/Shanghai' 
    AND posts.deleted_at is NULL
    AND reply_to_user_id = :target_user_id
    AND topics.archetype = 'regular'
    AND topics.deleted_at is NULL
    AND categories.read_restricted = False
    GROUP BY posts.user_id
)
SELECT l.from_user_id, 
    COALESCE(p.count,0)*5 + COALESCE(r.count,0)*1 + COALESCE(l.count,0)*2 as score,
    r.count as retort_count,
    l.count as like_count,
    p.count as reply_count
FROM r
FULL OUTER JOIN l
ON r.from_user_id = l.from_user_id
FULL OUTER JOIN p
ON r.from_user_id = p.from_user_id
WHERE l.from_user_id is not NULL
AND l.from_user_id > 0
AND l.from_user_id NOT IN (1,49425,24904)
ORDER BY score DESC
LIMIT 10