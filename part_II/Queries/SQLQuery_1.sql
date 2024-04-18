
with temp as(
SELECT u.userid, [country_name], SUM(iscorrect) as CorrectAnswers
FROM [Group_13].[Answers] AS a, [Group_13].[Users] AS u, [Group_13].[Geography] AS g
WHERE a.userid = u.userid AND u.geoid = g.geoid 
GROUP BY u.userid, country_name
)
SELECT country_name, max(CorrectAnswers) AS rank
FROM temp
GROUP BY country_name
ORDER BY rank DESC
