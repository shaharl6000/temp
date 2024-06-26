# -*- coding: utf-8 -*-
"""Untitled1.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1KS6NXPNTxEHIoYMV9HtQSW5dxxS7v9Jq
"""

# ! pip install datasets
# ! pip install evaluate
# ! pip install accelerate -U
# !pip install ipdb
# ! pip install peft

import evaluate
import numpy as np
from datasets import load_dataset
import transformers
from transformers import (AutoModelForSequenceClassification, AutoModelForCausalLM, AutoTokenizer)
# import ipdb
import torch
from torch.utils.data import DataLoader
from transformers import AdamW, get_scheduler
from tqdm import tqdm
from peft import LoraConfig, get_peft_model, TaskType


""" --------------------------------------- Q2 --------------------------------------- """
experiment_params = {
    "full_FT_1": {"IS_LORA": False, "LEARNING_RATE": 5e-5, "LORA_R": 0, "BATCH_SIZE": 8, "NUM_EPOCHS": 3, "MODEL": "microsoft/deberta-v3-base"},
    "full_FT_2": {"IS_LORA": False, "LEARNING_RATE": 1e-5, "LORA_R": 0, "BATCH_SIZE": 8, "NUM_EPOCHS": 5, "MODEL": "microsoft/deberta-v3-base"},
    "full_FT_3": {"IS_LORA": False, "LEARNING_RATE": 1e-5, "LORA_R": 0, "BATCH_SIZE": 32, "NUM_EPOCHS": 2, "MODEL": "microsoft/deberta-v3-base"},
    "lora_FT_1": {"IS_LORA": True, "LEARNING_RATE": 0.01, "LORA_R": 32, "BATCH_SIZE": 32, "NUM_EPOCHS": 2, "MODEL": 'microsoft/deberta-v3-base'},
    "lora_FT_2": {"IS_LORA": True, "LEARNING_RATE": 0.01, "LORA_R": 32, "BATCH_SIZE": 32, "NUM_EPOCHS": 2, "MODEL": 'microsoft/deberta-v3-base'},
    "lora_FT_3": {"IS_LORA": True, "LEARNING_RATE": 0.01, "LORA_R": 4, "BATCH_SIZE": 32, "NUM_EPOCHS": 2, "MODEL": 'microsoft/deberta-v3-base'},
    "deberta_large": {"IS_LORA": True, "LEARNING_RATE": 0.01, "LORA_R": 4, "BATCH_SIZE": 1, "NUM_EPOCHS": 2, "MODEL": "microsoft/deberta-v3-large"},
    "gemma": {"IS_LORA": True, "LEARNING_RATE": 0.01, "LORA_R": 4, "BATCH_SIZE": 1, "NUM_EPOCHS": 2, "MODEL": 'google/gemma-2b'}
}

hf_token = "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"

def run_experiment(experiment_name):

  if(experiment_name not in experiment_params):
    print("Invalid experiment name")
    return

  # Retrieve parameters for the selected experiment
  params = experiment_params[experiment_name]

  tokenizer = AutoTokenizer.from_pretrained(params["MODEL"])
  model = AutoModelForSequenceClassification.from_pretrained(params["MODEL"]).cuda()

  if (params["IS_LORA"]):
      lora_config = LoraConfig(
          task_type=TaskType.SEQ_CLS,
          r=params["LORA_R"],
          lora_alpha=4)

      # Apply LoRA
      model = get_peft_model(model, lora_config)
      model.print_trainable_parameters()

  def preprocess_function(examples):
      return tokenizer(
          examples['sentence1'],
          examples['sentence2'],
          max_length=128,
          truncation=True,
          padding='max_length'
      )

  # Load dataset and preprocess
  raw_datasets = load_dataset("glue", 'mrpc')
  tokenized_datasets = raw_datasets.map(preprocess_function, batched=True)
  tokenized_datasets = tokenized_datasets.remove_columns(['sentence1', 'sentence2', 'idx'])


  # Convert to PyTorch tensors
  tokenized_datasets.set_format("torch")

  train_dataset = tokenized_datasets["train"]
  eval_dataset = tokenized_datasets["validation"]

  train_dataloader = DataLoader(train_dataset, shuffle=True, batch_size=params["BATCH_SIZE"])
  eval_dataloader = DataLoader(eval_dataset, batch_size=params["BATCH_SIZE"])

  # third experiment:
  optimizer = AdamW(model.parameters(), lr=params["LEARNING_RATE"])
  num_epochs = params["NUM_EPOCHS"]

  num_training_steps = num_epochs * len(train_dataloader)
  lr_scheduler = get_scheduler(
      "linear",
      optimizer=optimizer,
      num_warmup_steps=0,
      num_training_steps=num_training_steps
  )

  print("TRAINING")
  model.train()
  for epoch in range(num_epochs):
      print(f"Epoch {epoch+1}/{num_epochs}")
      progress_bar = tqdm(train_dataloader, desc="Training")

      for batch in progress_bar:
          batch = {k: v.cuda() for k, v in batch.items()}
          batch['labels'] = batch.pop('label')
          outputs = model(**batch)
          loss = outputs.loss
          loss.backward()
          optimizer.step()
          lr_scheduler.step()
          optimizer.zero_grad()

      print(f"Epoch {epoch+1}/{num_epochs} completed")

  print("EVALUATING")
  model.eval()
  total_correct = 0
  total_samples = 0

  progress_bar = tqdm(eval_dataloader, desc="Evaluating")
  for batch in progress_bar:
      batch = {k: v.cuda() for k, v in batch.items()}
      batch['labels'] = batch.pop('label')
      with torch.no_grad():
          outputs = model(**batch)
      predictions = outputs.logits.argmax(dim=-1)
      labels = batch['labels']
      total_correct += (predictions == labels).sum().item()
      total_samples += labels.size(0)

  accuracy = total_correct / total_samples
  print(f"Validation Accuracy: {accuracy:.4f}")

"""  Q2.1  """

print("------------------ run full_FT_1 ------------------")
run_experiment("full_FT_1")
print("------------------ run full_FT_2 ------------------")
run_experiment("full_FT_2")
print("------------------ run full_FT_3 ------------------")
run_experiment("full_FT_3")

"""  Q2.2  """

print("------------------ run lora_FT_1 ------------------")
run_experiment("lora_FT_1")
print("------------------ run lora_FT_2 ------------------")
run_experiment("lora_FT_2")
print("------------------ run lora_FT_3 ------------------")
run_experiment("lora_FT_3")

"""  Q2.3  """

print("------------------ run deberta_large ------------------")
run_experiment("deberta_large")
print("------------------ run gemma ------------------")
run_experiment("gemma")

""" --------------------------------------- Q3 --------------------------------------- """

model = AutoModelForCausalLM.from_pretrained('microsoft/phi-2', token=access_token).cuda()
tokenizer = AutoTokenizer.from_pretrained('microsoft/phi-2', token=access_token)

def get_tokenized_list(prompt, list_topics):
  tokenized_list = []
  for topic in list_topics:
      tokenized_list.append(tokenizer(
          prompt + topic,
          return_tensors="pt",
          return_attention_mask=False
      ))
  return tokenized_list

prompt = "please write in exactly 230-240 words a summary about "
list_topics = ["Artificial Intelligence", "Climate Change", "Quantum Computing", "Virtual Reality", "Cryptocurrency", "Renewable Energy", "Space Exploration", "Genetic Engineering", "Mental Health", "Cybersecurity", "Autonomous Vehicles", "Blockchain Technology", "Augmented Reality", "Sustainable Agriculture", "Human-Computer Interaction", "Smart Cities", "Internet of Things", "Big Data Analytics", "Machine Learning", "3D Printing", "E-commerce", "Wearable Technology", "Telemedicine", "Digital Marketing", "E-learning", "Social Media Trends", "Fintech Innovations", "Biotechnology", "Green Building", "Clean Water Access", "Electric Vehicles", "Nanotechnology", "Robotics", "Food Security", "Urbanization", "Global Health", "Education Technology", "Workplace Automation", "Renewable Materials", "Disaster Preparedness", "Public Transportation", "Ocean Conservation", "Wildlife Protection", "Nuclear Fusion", "Astrobiology", "Renewable Energy Storage", "Telecommuting", "Aerospace Engineering", "Digital Privacy", "Open Source Software", "Virtual Collaboration", "Online Privacy", "Sustainable Fashion", "Pharmaceutical Advancements", "Carbon Footprint Reduction", "Renewable Energy Policy", "Cultural Heritage Preservation", "Bioinformatics", "Renewable Energy Integration", "Circular Economy"]
tokenized_list = get_tokenized_list(prompt, list_topics)
outputs_words_count = []

for t in tokenized_list:
  input = {k: v.cuda() for k, v in t.items()}
  cur_output = model.generate(**input, max_length=350)
  outputs_words_count.append(len(cur_output.split(" ")))
  print(len(cur_output.split(" ")))
  print(cur_output)
