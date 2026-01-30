import numpy as np
import base64
from io import BytesIO
from PIL import Image

class FaceEmbedder:
    def __init__(self):
        # Initialize your face embedding model here
        # This is a placeholder - replace with your actual model
        self.embedding_size = 512

    def generate_embedding(self, image_data):
        """
        Generate embedding from base64 image data
        Replace this with your actual face embedding model
        """
        try:
            # Convert base64 to image
            if image_data.startswith('data:image'):
                image_data = image_data.split(',')[1]
            image_bytes = base64.b64decode(image_data)
            image = Image.open(BytesIO(image_bytes))
            image = np.array(image)
            embedding = np.random.randn(self.embedding_size).astype(np.float32)    # Your face detection and embedding generation logic here
            embedding = embedding / np.linalg.norm(embedding)    # Normalize embedding (important for vector similarity)
            return embedding
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return None

    def generate_user_embeddings(self, photos_dict):
        """
        Generate concatenated embeddings from 5 angles
        Returns: concatenated vector [front + right + left + top + bottom]
        """
        embedding_order = ['front', 'right', 'left', 'top', 'bottom']
        all_embeddings = []
        for angle in embedding_order:
            if angle in photos_dict and photos_dict[angle]:
                embedding = self.generate_embedding(photos_dict[angle])
                if embedding is not None:
                    all_embeddings.extend(embedding.tolist())
                else:
                    all_embeddings.extend([0.0] * self.embedding_size)  # If embedding fails, use zeros
            else:
                all_embeddings.extend([0.0] * self.embedding_size)  # If angle missing, use zeros
        return all_embeddings  # Returns 2560-dimensional vector
