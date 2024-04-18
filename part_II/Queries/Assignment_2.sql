--- ASSIGNMENT 2
--- For each country, the student or students that answered the most questions correctly for that country.

WITH temp AS (
SELECT u.userid, [country_name],
     RANK() OVER (PARTITION BY [country_name] ORDER BY SUM([iscorrect]) DESC) AS rank_tot
FROM [Group_13].[Answers] AS a, [Group_13].[Users] AS u, [Group_13].[Geography] AS g
WHERE a.userid = u.userid AND u.geoid = g.geoid 
GROUP BY u.userid, country_name
  )
SELECT userid, country_name, rank_tot
FROM temp
WHERE rank_tot <= 3
ORDER BY country_name, rank_tot


