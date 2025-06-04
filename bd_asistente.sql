-- --------------------------------------------------------
-- Host:                         127.0.0.1
-- Versión del servidor:         10.4.32-MariaDB - mariadb.org binary distribution
-- SO del servidor:              Win64
-- HeidiSQL Versión:             12.8.0.6908
-- --------------------------------------------------------

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET NAMES utf8 */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;


-- Volcando estructura de base de datos para cul_chatbot_db
CREATE DATABASE IF NOT EXISTS `cul_chatbot_db` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci */;
USE `cul_chatbot_db`;

-- Volcando estructura para tabla cul_chatbot_db.faqs
CREATE TABLE IF NOT EXISTS `faqs` (
  `id` varchar(50) NOT NULL COMMENT 'ID único de la FAQ (ej: FAQ-MAT001)',
  `question` text NOT NULL COMMENT 'La pregunta frecuente',
  `answer` text NOT NULL COMMENT 'La respuesta a la pregunta',
  `category` varchar(100) DEFAULT 'General' COMMENT 'Categoría de la FAQ (ej: Matrículas, Bienestar)',
  `keywords` text DEFAULT NULL COMMENT 'Palabras clave para búsqueda, separadas por comas o como JSON string',
  `created_at` timestamp NOT NULL DEFAULT current_timestamp() COMMENT 'Fecha y hora de creación',
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp() COMMENT 'Fecha y hora de la última actualización',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='Tabla para almacenar Preguntas Frecuentes (FAQs)';

-- Volcando datos para la tabla cul_chatbot_db.faqs: ~6 rows (aproximadamente)
REPLACE INTO `faqs` (`id`, `question`, `answer`, `category`, `keywords`, `created_at`, `updated_at`) VALUES
	('FAQ-BIB001', '¿Cuál es el horario de la biblioteca?', 'El horario de la biblioteca principal es de Lunes a Viernes de 7:00 AM a 9:00 PM y Sábados de 8:00 AM a 4:00 PM. Estos horarios pueden variar en periodos de vacaciones o exámenes.', 'Servicios', 'biblioteca,horario,atención', '2025-06-04 18:38:31', '2025-06-04 18:38:31'),
	('FAQ-CUL001', '¿Qué es la CUL?', 'La Corporación Universitaria Latinoamericana (CUL) es una institución de educación superior comprometida con la formación integral de profesionales. Ofrecemos programas de pregrado y posgrado en diversas áreas del conocimiento.', 'General CUL', 'cul,universidad,quienes somos', '2025-06-04 18:38:31', '2025-06-04 18:38:31'),
	('FAQ-HOR001', '¿Dónde puedo consultar los horarios de clase?', 'Los horarios de clase se publican en la plataforma virtual de la universidad (Moodle o similar) antes del inicio de cada semestre. También puedes acercarte a la secretaría de tu facultad.', 'Académico', 'horarios,clases,semestre,plataforma', '2025-06-04 18:38:31', '2025-06-04 18:38:31'),
	('FAQ-MAT001', '¿Cuáles son los requisitos para la inscripción a un pregrado?', 'Generalmente necesitas: copia de tu documento de identidad, resultados de pruebas Saber 11 (ICFES), diploma de bachiller y acta de grado. Consulta la página de admisiones para detalles específicos del programa.', 'Admisiones', 'inscripción,requisitos,pregrado,admisión', '2025-06-04 18:38:31', '2025-06-04 18:38:31'),
	('FAQ-PAG001', '¿Cuáles son los métodos de pago para la matrícula?', 'Puedes pagar tu matrícula en línea a través de PSE, con tarjeta de crédito/débito en la plataforma de pagos, o directamente en las entidades bancarias autorizadas. Consulta la sección de pagos en la web para más detalles.', 'Pagos', 'matrícula,pago,métodos,banco,pse', '2025-06-04 18:38:31', '2025-06-04 18:38:31'),
	('FAQ-SOP001', 'No puedo acceder a mi correo institucional, ¿qué hago?', 'Primero, intenta restablecer tu contraseña desde el portal de autoservicio. Si el problema persiste, contacta a la mesa de ayuda de TI o genera un ticket de soporte técnico.', 'Soporte Técnico', 'correo,contraseña,acceso,soporte', '2025-06-04 18:38:31', '2025-06-04 18:38:31');

-- Volcando estructura para tabla cul_chatbot_db.tickets
CREATE TABLE IF NOT EXISTS `tickets` (
  `id` varchar(36) NOT NULL COMMENT 'ID único del ticket (UUID)',
  `user_id_telegram` varchar(100) DEFAULT NULL COMMENT 'ID del usuario en Telegram',
  `user_name_telegram` varchar(255) DEFAULT NULL COMMENT 'Nombre del usuario en Telegram',
  `user_email` varchar(255) DEFAULT NULL COMMENT 'Email de contacto del usuario',
  `problem_description` text NOT NULL COMMENT 'Descripción detallada del problema o consulta',
  `category` varchar(100) DEFAULT 'General' COMMENT 'Categoría del ticket (ej: Soporte Técnico, Admisiones)',
  `priority` varchar(50) DEFAULT 'Media' COMMENT 'Prioridad del ticket (ej: Alta, Media, Baja)',
  `status` varchar(50) NOT NULL DEFAULT 'Abierto' COMMENT 'Estado actual del ticket (ej: Abierto, En Proceso, Resuelto, Cerrado)',
  `source` varchar(100) DEFAULT 'Desconocido' COMMENT 'Origen del ticket (ej: Chatbot CUL Telegram)',
  `assigned_to` varchar(100) DEFAULT NULL COMMENT 'Agente o departamento asignado (opcional)',
  `resolution_details` text DEFAULT NULL COMMENT 'Detalles de la resolución del ticket (opcional)',
  `created_at` timestamp NOT NULL DEFAULT current_timestamp() COMMENT 'Fecha y hora de creación',
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp() COMMENT 'Fecha y hora de la última actualización',
  `closed_at` timestamp NULL DEFAULT NULL COMMENT 'Fecha y hora de cierre del ticket (opcional)',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='Tabla para almacenar los tickets de soporte';

-- Volcando datos para la tabla cul_chatbot_db.tickets: ~5 rows (aproximadamente)
REPLACE INTO `tickets` (`id`, `user_id_telegram`, `user_name_telegram`, `user_email`, `problem_description`, `category`, `priority`, `status`, `source`, `assigned_to`, `resolution_details`, `created_at`, `updated_at`, `closed_at`) VALUES
	('1e6572d8-50a8-4f7c-9f2a-6a9d8f3c2b1e', '123456789', 'Juan Perez (Telegram)', 'juan.perez@example.com', 'No puedo acceder a la plataforma Moodle, me dice usuario o contraseña incorrectos y ya intenté restablecerla.', 'Soporte Técnico', 'Alta', 'Abierto', 'Chatbot CUL Telegram', NULL, NULL, '2025-06-04 18:38:31', '2025-06-04 18:38:31', NULL),
	('27e08545-7361-4bb7-bbe7-3f9d3bb34edb', 'string', 'string', 'user@example.com', 'No me conecta mi email', 'General', 'Media', 'Abierto', 'Chatbot CUL', NULL, NULL, '2025-06-04 18:53:49', '2025-06-04 18:53:49', NULL),
	('2f7b83e1-41c9-4b8d-a0c3-7b0e9g4d3c2f', '987654321', 'Ana Gomez (Telegram)', 'ana.gomez@example.com', 'Quisiera saber si hay becas disponibles para el programa de Ingeniería de Sistemas y cuáles son los requisitos.', 'Admisiones', 'Media', 'Abierto', 'Chatbot CUL Telegram', NULL, NULL, '2025-06-04 18:38:31', '2025-06-04 18:38:31', NULL),
	('3a8c94f2-52d0-4c9e-b1d4-8c1f0h5e4d3g', '555111222', 'Carlos Lopez', 'c.lopez@email.xyz', 'Necesito un certificado de estudios para mi actual semestre, ¿cómo lo solicito y cuánto tarda?', 'Académico', 'Media', 'En Proceso', 'Formulario Web', NULL, NULL, '2025-06-04 18:38:31', '2025-06-04 18:38:31', NULL),
	('4b9d05a3-63e1-4daF-c2e5-9d2g1i6f5e4h', '777888999', 'Laura Rodriguez (TG)', NULL, 'El enlace para la clase de Cálculo Diferencial de hoy no funciona.', 'Soporte Técnico', 'Urgente', 'Abierto', 'Chatbot CUL Telegram', NULL, NULL, '2025-06-04 18:38:31', '2025-06-04 18:38:31', NULL);

/*!40103 SET TIME_ZONE=IFNULL(@OLD_TIME_ZONE, 'system') */;
/*!40101 SET SQL_MODE=IFNULL(@OLD_SQL_MODE, '') */;
/*!40014 SET FOREIGN_KEY_CHECKS=IFNULL(@OLD_FOREIGN_KEY_CHECKS, 1) */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40111 SET SQL_NOTES=IFNULL(@OLD_SQL_NOTES, 1) */;
