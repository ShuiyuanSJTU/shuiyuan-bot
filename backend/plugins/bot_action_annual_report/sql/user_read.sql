SELECT user_id,sum(posts_read) as posts_read,sum(time_read) as time_read,count(visited_at) as days_visited
FROM user_visits
WHERE visited_at >= '2024-1-1'
AND visited_at < '2025-1-1'
GROUP BY user_id
ORDER BY sum(time_read) DESC