from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import numpy as np
import logging
import asyncio
from typing import List
import tensorflow as tf
from keras import layers, models

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

class Metrics(BaseModel):
    followers: int
    songsReleased: int
    albumsReleased: int
    releaseFrequency: float
    totalLikes: int
    totalStreams: int
    totalComments: int
    totalVideos: int
    totalPhotos: int

class TrainingData(BaseModel):
    targetMetrics: Metrics
    compareMetrics: List[Metrics]

def build_mlp_model(input_shape):
    model = models.Sequential()
    model.add(layers.Input(shape=(input_shape,)))
    model.add(layers.Dense(128, activation='relu'))
    model.add(layers.Dense(64, activation='relu'))
    model.add(layers.Dense(32, activation='relu'))
    model.add(layers.Dense(1))
    return model

def train_mlp_model(X_train, y_train, epochs=100, batch_size=32):
    model = build_mlp_model(X_train.shape[1])
    model.compile(optimizer='adam', loss='mean_squared_error', metrics=['mae'])
    model.fit(X_train, y_train, epochs=epochs, batch_size=batch_size, validation_split=0.2, verbose=0)
    return model

async def calculate_improvement_effects(target: Metrics, medians: dict):
    improvements = {}

    for metric in medians:
        current_value = getattr(target, metric)
        median = medians[metric]

        if metric == 'releaseFrequency':
            improved_value = min(median * 0.9, current_value * 0.9)
        else:
            improved_value = max(median * 1.2, current_value * 1.2)

        if metric != 'releaseFrequency':
            improved_value = max(improved_value, current_value)
        else:
            improved_value = min(improved_value, current_value)

        if metric in ['followers', 'songsReleased', 'albumsReleased', 'totalLikes', 'totalComments', 'totalVideos', 'totalPhotos']:
            improved_value = int(round(improved_value))

        target_improved = target.model_dump()
        target_improved[metric] = improved_value
        improvements[metric] = Metrics(**target_improved)

    return improvements

async def predict_future_streams(training_data: TrainingData) -> dict:
    try:
        metrics = ['followers', 'songsReleased', 'albumsReleased', 'releaseFrequency', 
                   'totalLikes', 'totalComments', 'totalVideos', 'totalPhotos']
        
        medians = {}
        for metric in metrics:
            values = np.array([getattr(m, metric) for m in training_data.compareMetrics])
            medians[metric] = np.median(values)

        improvements = await calculate_improvement_effects(training_data.targetMetrics, medians)

        X_train = np.array([[m.followers, m.songsReleased, m.albumsReleased, m.releaseFrequency, m.totalLikes, m.totalStreams, m.totalComments, m.totalVideos, m.totalPhotos] for m in training_data.compareMetrics])
        y_train = np.array([m.totalStreams for m in training_data.compareMetrics])
        model = await asyncio.to_thread(train_mlp_model, X_train, y_train)

        predictions = {}
        for metric, improved_target in improvements.items():
            target_data = np.array([[improved_target.followers, improved_target.songsReleased, improved_target.albumsReleased, improved_target.releaseFrequency, improved_target.totalLikes, improved_target.totalStreams, improved_target.totalComments, improved_target.totalVideos, improved_target.totalPhotos]])
            prediction = await asyncio.to_thread(model.predict, target_data)
            prediction_value = float(prediction[0][0])
            if prediction_value < improved_target.totalStreams:
                prediction_value = improved_target.totalStreams

            predictions[metric] = {
                'predicted_value': prediction_value,
                'improved_value': getattr(improved_target, metric)
            }

        logger.info(f"Predictions: {predictions}")
        return predictions
    
    except Exception as e:
        logger.error(f"An error occurred during training and prediction: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))