import json
import base64
import os
import logging
from io import BytesIO
from PIL import Image
import boto3

# Configurer le logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client('s3')


def lambda_handler(event, context):
    try:
        logger.info("Début du traitement de l'image")

        # Vérifier si le body est présent
        if 'body' not in event:
            raise ValueError("Body manquant dans la requête")

        # Récupérer l'image depuis le body de la requête
        body = json.loads(event['body'])

        if 'image' not in body:
            raise ValueError("Clé 'image' manquante dans le body")

        logger.info("Image reçue, début du décodage base64")
        image_data = base64.b64decode(body['image'])
        logger.info("Image décodée avec succès")

        # Ouvrir l'image avec Pillow
        image = Image.open(BytesIO(image_data))
        logger.info(f"Image ouverte avec succès. Format: {image.format}, Taille: {image.size}")

        # Redimensionner l'image (par exemple à 800x600)
        resized_image = image.resize((800, 600), Image.LANCZOS)
        logger.info("Image redimensionnée avec succès")

        # Convertir l'image redimensionnée en bytes
        output_buffer = BytesIO()
        resized_image.save(output_buffer, format=image.format)
        output_buffer.seek(0)
        logger.info("Image convertie en bytes avec succès")

        # Générer un nom de fichier unique
        file_name = f"resized_{int(context.get_remaining_time_in_millis())}.{image.format.lower()}"
        logger.info(f"Nom de fichier généré: {file_name}")

        # Upload vers S3
        bucket_name = os.environ['DESTINATION_BUCKET']
        logger.info(f"Upload vers le bucket: {bucket_name}")

        s3.put_object(
            Bucket=bucket_name,
            Key=file_name,
            Body=output_buffer,
            ContentType=f'image/{image.format.lower()}'
        )
        logger.info("Upload vers S3 réussi")

        # Générer l'URL de l'image (presigned url)
        # image_url = f"https://{bucket_name}.s3.amazonaws.com/{file_name}"
        image_url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': file_name},
            ExpiresIn=3600  # 1h
        )
        logger.info(f"URL de l'image générée: {image_url}")

        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Credentials': True,
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'message': 'Image redimensionnée avec succès',
                'imageUrl': image_url
            })
        }

    except json.JSONDecodeError as e:
        logger.error(f"Erreur de décodage JSON: {str(e)}")
        return {
            'statusCode': 400,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Credentials': True,
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'message': f'Erreur de format de requête: {str(e)}'
            })
        }
    except ValueError as e:
        logger.error(f"Erreur de validation: {str(e)}")
        return {
            'statusCode': 400,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Credentials': True,
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'message': f'Erreur de validation: {str(e)}'
            })
        }
    except Exception as e:
        logger.error(f"Erreur inattendue: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Credentials': True,
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'message': f'Erreur lors du traitement de l\'image: {str(e)}'
            })
        }
