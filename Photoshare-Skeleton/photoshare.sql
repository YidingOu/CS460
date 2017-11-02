CREATE DATABASE pa1;


DROP TABLE IF EXISTS `albums`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `albums` (
  `album_id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(45) NOT NULL,
  `owner_d` int(11) NOT NULL,
  `date_of_creation` varchar(45) NOT NULL,
  PRIMARY KEY (`album_id`),
  KEY `owner_id_idx` (`owner_d`),
  CONSTRAINT `id` FOREIGN KEY (`owner_d`) REFERENCES `users` (`user_id`) ON DELETE CASCADE ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


DROP TABLE IF EXISTS `comments`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `comments` (
  `comment_id` int(11) NOT NULL AUTO_INCREMENT,
  `text` varchar(45) NOT NULL,
  `owener` int(11) NOT NULL,
  `date` varchar(45) NOT NULL,
  `photoid` int(11) NOT NULL,
  PRIMARY KEY (`comment_id`),
  KEY `user_email_idx` (`owener`),
  KEY `photo_comment_idx` (`photoid`),
  CONSTRAINT `photo_comment` FOREIGN KEY (`photoid`) REFERENCES `photos` (`photo_id`) ON DELETE CASCADE ON UPDATE NO ACTION,
  CONSTRAINT `user_email` FOREIGN KEY (`owener`) REFERENCES `users` (`user_id`) ON DELETE CASCADE ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

DROP TABLE IF EXISTS `friend`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `friend` (
  `user_id` int(11) NOT NULL,
  `friend_id` int(11) NOT NULL,
  KEY `friend_idx` (`friend_id`),
  KEY `user_idx` (`user_id`),
  CONSTRAINT `friend` FOREIGN KEY (`friend_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE ON UPDATE NO ACTION,
  CONSTRAINT `user` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


DROP TABLE IF EXISTS `likes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `likes` (
  `user` int(11) NOT NULL,
  `photo_id` int(11) NOT NULL,
  KEY `user_idx` (`user`),
  KEY `photo_idx` (`photo_id`),
  CONSTRAINT `photo` FOREIGN KEY (`photo_id`) REFERENCES `photos` (`photo_id`) ON DELETE CASCADE ON UPDATE NO ACTION,
  CONSTRAINT `uid` FOREIGN KEY (`user`) REFERENCES `users` (`user_id`) ON DELETE CASCADE ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


DROP TABLE IF EXISTS `photos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `photos` (
  `photo_id` int(11) NOT NULL AUTO_INCREMENT,
  `caption` varchar(45) NOT NULL,
  `imgdata` blob NOT NULL,
  `album_id` int(11) NOT NULL,
  `owner` int(11) NOT NULL,
  PRIMARY KEY (`photo_id`),
  KEY `album_id_idx` (`album_id`),
  KEY `owner_idx` (`owner`),
  CONSTRAINT `album` FOREIGN KEY (`album_id`) REFERENCES `albums` (`album_id`) ON DELETE CASCADE ON UPDATE NO ACTION,
  CONSTRAINT `owner_id` FOREIGN KEY (`owner`) REFERENCES `users` (`user_id`) ON DELETE CASCADE ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `users` (
  `user_id` int(11) NOT NULL AUTO_INCREMENT,
  `first_name` varchar(45) NOT NULL,
  `last_name` varchar(45) NOT NULL,
  `email` varchar(45) NOT NULL,
  `date_of_birth` varchar(45) NOT NULL,
  `hometown` varchar(45) NOT NULL,
  `gender` varchar(45) NOT NULL,
  `password` varchar(255) NOT NULL,
  PRIMARY KEY (`user_id`),
  UNIQUE KEY `email_UNIQUE` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8;


DROP TABLE IF EXISTS `tags`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tags` (
  `text` varchar(255) NOT NULL,
  `photo_id` int(11) NOT NULL,
  KEY `photo_id_idx` (`photo_id`),
  CONSTRAINT `photo_id` FOREIGN KEY (`photo_id`) REFERENCES `photos` (`photo_id`) ON DELETE CASCADE ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
