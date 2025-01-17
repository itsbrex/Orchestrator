# -*- coding: utf-8 -*-
"""Orchestrator_Composer.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/github/asigalov61/Orchestrator/blob/main/Orchestrator_Composer.ipynb

# Orchestrator Composer (ver. 2.5)

***

Powered by tegridy-tools: https://github.com/asigalov61/tegridy-tools

***

WARNING: This complete implementation is a functioning model of the Artificial Intelligence. Please excercise great humility, care, and respect. https://www.nscai.gov/

***

#### Project Los Angeles

#### Tegridy Code 2022

***

# (GPU CHECK)
"""

#@title NVIDIA GPU check
!nvidia-smi

"""# (SETUP ENVIRONMENT)"""

#@title Install dependencies
!git clone --depth 1 https://github.com/asigalov61/Orchestrator
!pip install torch
!pip install einops
!pip install torch-summary
!pip install tqdm
!pip install matplotlib
!apt install fluidsynth #Pip does not work for some reason. Only apt works
!pip install midi2audio

# Commented out IPython magic to ensure Python compatibility.
#@title Import modules

print('=' * 70)
print('Loading core Orchestrator modules...')

import os
import pickle
import random
import secrets
import statistics
from time import time
import tqdm

print('=' * 70)
print('Loading main Orchestrator modules...')
import torch

# %cd /content/Orchestrator

import TMIDIX

from lwa_transformer import *

# %cd /content/
print('=' * 70)
print('Loading aux Orchestrator modeules...')

import matplotlib.pyplot as plt

from torchsummary import summary
from sklearn import metrics


from midi2audio import FluidSynth
from IPython.display import Audio, display

from google.colab import files

print('=' * 70)
print('Done!')
print('Enjoy! :)')
print('=' * 70)

"""# (LOAD MODEL)"""

# Commented out IPython magic to ensure Python compatibility.
#@title Unzip Pre-Trained Orchestrator Model
print('=' * 70)
# %cd /content/Orchestrator/Model

print('=' * 70)
print('Unzipping pre-trained Orchestartor model...Please wait...')

!cat /content/Orchestrator/Model/Orchestrator_Trained_Model_55253_steps_0.3277_loss.zip* > /content/Orchestrator/Model/Orchestrator_Trained_Model_55253_steps_0.3277_loss.zip
print('=' * 70)

!unzip -j /content/Orchestrator/Model/Orchestrator_Trained_Model_55253_steps_0.3277_loss.zip
print('=' * 70)

print('Done! Enjoy! :)')
print('=' * 70)
# %cd /content/
print('=' * 70)

#@title Load Orchestrator Pre-Trained Model
full_path_to_model_checkpoint = "/content/Orchestrator/Model/Orchestrator_Trained_Model_55253_steps_0.3277_loss.pth" #@param {type:"string"}

#@markdown Model precision option

model_precision = "bfloat16" # @param ["bfloat16", "float16", "float32"]

#@markdown bfloat16 == Third precision/triple speed (if supported, otherwise the model will default to float16)

#@markdown float16 == Half precision/double speed

#@markdown float32 == Full precision/normal speed

plot_tokens_embeddings = False # @param {type:"boolean"}

print('=' * 70)
print('Loading Orchestrator Pre-Trained Model...')
print('Please wait...')
print('=' * 70)
print('Instantiating model...')

torch.backends.cuda.matmul.allow_tf32 = True # allow tf32 on matmul
torch.backends.cudnn.allow_tf32 = True # allow tf32 on cudnn
device_type = 'cuda'

if model_precision == 'bfloat16' and torch.cuda.is_bf16_supported():
  dtype = 'bfloat16'
else:
  dtype = 'float16'

if model_precision == 'float16':
  dtype = 'float16'

if model_precision == 'float32':
  dtype = 'float32'

ptdtype = {'float32': torch.float32, 'bfloat16': torch.bfloat16, 'float16': torch.float16}[dtype]
ctx = torch.amp.autocast(device_type=device_type, dtype=ptdtype)

SEQ_LEN = 4096

# instantiate the model

model = LocalTransformer(
    num_tokens = 774,
    dim = 1024,
    depth = 24,
    causal = True,
    local_attn_window_size = 512,
    max_seq_len = SEQ_LEN
).cuda()
print('=' * 70)

print('Loading model checkpoint...')

model.load_state_dict(torch.load(full_path_to_model_checkpoint))
print('=' * 70)

model.eval()

print('Done!')
print('=' * 70)

print('Model will use', dtype, 'precision...')
print('=' * 70)

# Model stats
print('Model summary...')
summary(model)

# Plot Token Embeddings

if plot_tokens_embeddings:
  tok_emb = model.token_emb.weight.detach().cpu().tolist()

  cos_sim = metrics.pairwise_distances(
    tok_emb, metric='cosine'
  )
  plt.figure(figsize=(7, 7))
  plt.imshow(cos_sim, cmap="inferno", interpolation="nearest")
  im_ratio = cos_sim.shape[0] / cos_sim.shape[1]
  plt.colorbar(fraction=0.046 * im_ratio, pad=0.04)
  plt.xlabel("Position")
  plt.ylabel("Position")
  plt.tight_layout()
  plt.plot()
  plt.savefig("/content/Orchestrator-Tokens-Embeddings-Plot.png", bbox_inches="tight")

"""# (LOAD SEED MIDI)"""

#@title Load Seed MIDI

#@markdown Press play button to to upload your own seed MIDI or to load one of the provided sample seed MIDIs from the dropdown list below

select_seed_MIDI = "Upload your own custom MIDI" #@param ["Upload your own custom MIDI", "Orchestrator-Piano-Seed-1", "Orchestrator-Piano-Seed-2", "Orchestrator-Piano-Seed-3", "Orchestrator-Piano-Seed-4", "Orchestrator-Piano-Seed-5", "Orchestrator-MI-Seed-1", "Orchestrator-MI-Seed-2", "Orchestrator-MI-Seed-3", "Orchestrator-MI-Seed-4", "Orchestrator-MI-Seed-5"]
number_of_prime_tokens = 384 # @param {type:"slider", min:384, max:2048, step:4}
render_MIDI_to_audio = False # @param {type:"boolean"}

print('=' * 70)
print('Orchestrator Seed MIDI Loader')
print('=' * 70)

f = ''

if select_seed_MIDI != "Upload your own custom MIDI":
  print('Loading seed MIDI...')
  f = '/content/Orchestrator/Seeds/'+select_seed_MIDI+'.mid'
  score = TMIDIX.midi2single_track_ms_score(open(f, 'rb').read(), recalculate_channels=False)

else:
  print('Upload your own custom MIDI...')
  print('=' * 70)
  uploaded_MIDI = files.upload()
  if list(uploaded_MIDI.keys()):
    score = TMIDIX.midi2single_track_ms_score(list(uploaded_MIDI.values())[0], recalculate_channels=False)
    f = list(uploaded_MIDI.keys())[0]

if f != '':

  print('=' * 70)
  print('File:', f)
  print('=' * 70)

  #=======================================================

  transpose_to_model_average_pitch = False

  #=======================================================
  # START PROCESSING

  # INSTRUMENTS CONVERSION CYCLE
  events_matrix = []
  melody_chords_f = []
  melody_chords_f1 = []
  itrack = 1
  patches = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

  patch_map = [[0, 1, 2, 3, 4, 5, 6, 7], # Piano
            [24, 25, 26, 27, 28, 29, 30], # Guitar
            [32, 33, 34, 35, 36, 37, 38, 39], # Bass
            [40, 41], # Violin
            [42, 43], # Cello
            [46], # Harp
            [56, 57, 58, 59, 60], # Trumpet
            [71, 72], # Clarinet
            [73, 74, 75], # Flute
            [-1], # Drums
            [52, 53], # Choir
            [16, 17, 18, 19, 20] # Organ
            ]

  while itrack < len(score):
    for event in score[itrack]:
        if event[0] == 'note' or event[0] == 'patch_change':
            events_matrix.append(event)
    itrack += 1

  events_matrix.sort(key=lambda x: x[1])

  events_matrix1 = []

  for event in events_matrix:
    if event[0] == 'patch_change':
        patches[event[2]] = event[3]

    if event[0] == 'note':
        event.extend([patches[event[3]]])
        once = False

        for p in patch_map:
            if event[6] in p and event[3] != 9: # Except the drums
                event[3] = patch_map.index(p)
                once = True

        if not once and event[3] != 9: # Except the drums
            event[3] = 15 # All other instruments/patches channel
            event[5] = max(80, event[5])

        if event[3] < 12: # We won't write chans 12-16 for now...
            events_matrix1.append(event)
            # stats[event[3]] += 1

  #=======================================================
  # PRE-PROCESSING

  # checking number of instruments in a composition
  instruments_list_without_drums = list(set([y[3] for y in events_matrix1 if y[3] != 9]))

  instruments_list = list(set([y[3] for y in events_matrix1]))
  num_instr = len(instruments_list)

  # filtering out empty compositions and checking desired number of instruments in a composition
  # It had been observed that music models learn best from multi-instrumental music, even for solo instruments
  # So you can setup filtering by number of instruments here if you want

  if len(events_matrix1) > 0 and len(instruments_list_without_drums) > 0:

      # recalculating timings
      for e in events_matrix1:
          e[1] = int(e[1] / 8) # Max 1 seconds for start-times
          e[2] = int(e[2] / 16) # Max 2 seconds for durations

      # Sorting by pitch, then by start-time
      events_matrix1.sort(key=lambda x: x[4], reverse=True)
      events_matrix1.sort(key=lambda x: x[1])

      # pitches augment stuff (calculating transpose value to C4 without drums)
      pitches = [y[4] for y in events_matrix1 if y[3] != 9]

      if len(pitches) > 0:
        avg_ptc = round(statistics.mean(pitches))
      else:
        avg_ptc = 0

      ptc_delta = 12 - (avg_ptc % 12)

      #=======================================================
      # FINAL PRE-PROCESSING

      first_event = True
      melody_chords = []
      pe = events_matrix1[0]
      pt = -1

      for e in events_matrix1:

          # Cliping all values...
          tim = max(0, min(127, e[1]-pe[1]))
          dur = max(1, min(127, e[2]))
          cha = max(0, min(11, e[3]))
          ptc = max(1, min(127, e[4]))
          vel = max(8, min(127, e[5]))

          velocity = round(vel / 15)

          # Pitches shifting
          if cha != 9:
              if transpose_to_model_average_pitch:
                  ptc_aug = ptc + ptc_delta # Transposing composition to median C4
              else:
                  ptc_aug = ptc
          else:
            ptc_aug = ptc + 128 # Shifting drums pitches because drums structure is different from non-drums

          # Time shifting
          if tim == 0 and first_event == True:
            abs_time = 0

          if tim == 0 and first_event == False:
            if pt == 0:
              pass
            else:
              abs_time += 128

          if tim !=0:
            abs_time = tim

          # Writing final note
          melody_chords.append([abs_time, dur, cha, ptc_aug, velocity])

          pe = e
          pt = tim

          first_event = False

      #=======================================================
      # FINAL PROCESSING
      #=======================================================

      # Break between compositions / Intro seq

      # 758 == SOS/EOS token
      # 759 == SOS/EOS token
      # 760-761 == Composition is without drums or with drums
      # 762-773 == Number of instruments in a composition

      # TOTAL DICTIONARY SIZE OF 774 TOKENS

      if 9 in instruments_list:
        drums_present = 761 # Yes
      else:
        drums_present = 760 # No

      melody_chords_f.extend([758, 759, drums_present, 762+(num_instr-1)])
      melody_chords_f1.append([758, 759, drums_present, 762+(num_instr-1)])

      #=======================================================

      # Composition control seq
      intro_mode_time = statistics.mode([y[0] for y in melody_chords if y[2] != 9])
      intro_mode_dur = statistics.mode([y[1] for y in melody_chords if y[2] != 9])
      intro_mode_pitch = statistics.mode([y[3] for y in melody_chords if y[2] != 9])
      intro_mode_velocity = statistics.mode([y[4] for y in melody_chords if y[2] != 9])

      # Instrument value 12 is reserved for composition control seq
      intro_vel = (12 * 9) + intro_mode_velocity

      melody_chords_f.extend([intro_mode_time, intro_mode_dur+256, intro_mode_pitch+384, intro_vel+640])
      melody_chords_f1.append([intro_mode_time, intro_mode_dur+256, intro_mode_pitch+384, intro_vel+640])

      #=======================================================
      # MAIN PROCESSING CYCLE
      #=======================================================

      for m in melody_chords:

          # WRITING EACH NOTE HERE
          chan_vel = (m[2] * 9) + m[4]
          melody_chords_f.extend([m[0], m[1]+256, m[3]+384, chan_vel+640])
          melody_chords_f1.append([m[0], m[1]+256, m[3]+384, chan_vel+640])

  melody_chords_f1 = melody_chords_f1[:(number_of_prime_tokens // 4)]
  melody_chords_f = melody_chords_f[:number_of_prime_tokens]

  print('Composition stats:')
  print('Composition has', len(melody_chords_f1), 'notes')
  print('Composition has', len(melody_chords_f), 'tokens')
  print('=' * 70)

  #=======================================================

  song = melody_chords_f
  song_f = []
  tim = 0
  dur = 0
  vel = 0
  pitch = 0
  channel = 0

  son = []
  song1 = []

  for s in song:
    if s > 256 and s < (12*9)+640:
      son.append(s)
    else:
      if len(son) == 4:
        song1.append(son)
      son = []
      son.append(s)

  for ss in song1:

      if ss[0] < 128:
        tim += ss[0] * 8

      dur = (ss[1]-256) * 16

      if (ss[2]-384) > 128:
        pitch = (ss[2]-384) - 128
      else:
        pitch = (ss[2]-384)


      channel = (ss[3]-640) // 9
      vel = ((ss[3]-640) % 9) * 15

      song_f.append(['note', tim, dur, channel, pitch, vel ])

  detailed_stats = TMIDIX.Tegridy_ms_SONG_to_MIDI_Converter(song_f,
                                                            output_signature = 'Orchestrator',
                                                            output_file_name = '/content/Orchestrator-Seed-Composition',
                                                            track_name='Project Los Angeles',
                                                            list_of_MIDI_patches=[0, 24, 32, 40, 42, 46, 56, 71, 73, 0, 53, 19, 0, 0, 0, 0]
                                                            )

  #=======================================================

  print('=' * 70)
  print('Displaying resulting composition...')
  print('=' * 70)

  fname = '/content/Orchestrator-Seed-Composition'

  x = []
  y =[]
  c = []

  colors = ['red', 'yellow', 'green', 'cyan', 'blue', 'pink', 'orange', 'purple', 'gray', 'white', 'gold', 'silver']

  block_lines = [(song_f[-1][1] / 1000)]

  for s in song_f:
    x.append(s[1] / 1000)
    y.append(s[4])
    c.append(colors[s[3]])

  if render_MIDI_to_audio:
    FluidSynth("/usr/share/sounds/sf2/FluidR3_GM.sf2", 16000).midi_to_audio(str(fname + '.mid'), str(fname + '.wav'))
    display(Audio(str(fname + '.wav'), rate=16000))

  plt.figure(figsize=(14,5))
  ax=plt.axes(title=fname)
  ax.set_facecolor('black')

  plt.scatter(x,y, c=c)
  plt.xlabel("Time")
  plt.ylabel("Pitch")
  plt.show()

else:
  print('=' * 70)

"""# (COMPOSITION LOOP)

## Run the cells below in a loop to generate endless continuation
"""

#@title Standard Continuation Generator

#@markdown Generation settings

number_of_batches_to_generate = 4 #@param {type:"slider", min:1, max:16, step:1}
number_of_memory_tokens = 4096 # @param {type:"slider", min:128, max:4096, step:4}
temperature = 0.8 #@param {type:"slider", min:0.1, max:1, step:0.1}

#@markdown Other settings
render_MIDI_to_audio = True # @param {type:"boolean"}

print('=' * 70)
print('Orchestrator Standard Continuation Model Generator')
print('=' * 70)

inp = [melody_chords_f[-number_of_memory_tokens:]] * number_of_batches_to_generate

inp = torch.LongTensor(inp).cuda()

with ctx:
  out = model.generate(inp,
                        384,
                        temperature=temperature,
                        return_prime=False,
                        verbose=True)

out0 = out.tolist()

print('=' * 70)
print('Done!')

#======================================================================

print('=' * 70)
print('Rendering results...')

for i in range(number_of_batches_to_generate):

  print('=' * 70)
  print('Batch #', i)
  print('=' * 70)

  out1 = out0[i]

  print('Sample INTs', out1[:12])
  print('=' * 70)

  if len(out) != 0:

      song = out1
      song_f = []
      tim = 0
      dur = 0
      vel = 0
      pitch = 0
      channel = 0

      son = []
      song1 = []

      for s in song:
        if s > 256 and s < (12*9)+640:
          son.append(s)
        else:
          if len(son) == 4:
            song1.append(son)
          son = []
          son.append(s)


      for ss in song1:

          if ss[0] < 128:
            tim += ss[0] * 8

          dur = (ss[1]-256) * 16

          if (ss[2]-384) > 128:
            pitch = (ss[2]-384) - 128
          else:
            pitch = (ss[2]-384)


          channel = (ss[3]-640) // 9
          vel = ((ss[3]-640) % 9) * 15

          song_f.append(['note', tim, dur, channel, pitch, vel ])

      detailed_stats = TMIDIX.Tegridy_ms_SONG_to_MIDI_Converter(song_f,
                                                                output_signature = 'Orchestrator',
                                                                output_file_name = '/content/Orchestrator-Music-Composition_'+str(i),
                                                                track_name='Project Los Angeles',
                                                                list_of_MIDI_patches=[0, 24, 32, 40, 42, 46, 56, 71, 73, 0, 53, 19, 0, 0, 0, 0])

      print('=' * 70)
      print('Displaying resulting composition...')
      print('=' * 70)

      fname = '/content/Orchestrator-Music-Composition_'+str(i)

      x = []
      y =[]
      c = []

      colors = ['red', 'yellow', 'green', 'cyan', 'blue', 'pink', 'orange', 'purple', 'gray', 'white', 'gold', 'silver']

      for s in song_f:
        x.append(s[1] / 1000)
        y.append(s[4])
        c.append(colors[s[3]])

      if render_MIDI_to_audio:
        FluidSynth("/usr/share/sounds/sf2/FluidR3_GM.sf2", 16000).midi_to_audio(str(fname + '.mid'), str(fname + '.wav'))
        display(Audio(str(fname + '.wav'), rate=16000))

      plt.figure(figsize=(14,5))
      ax=plt.axes(title=fname)
      ax.set_facecolor('black')

      plt.scatter(x,y, c=c)
      plt.xlabel("Time")
      plt.ylabel("Pitch")
      plt.show()

#@title Choose one generated block to add to the composition
block_action = "add_last_generated_block" #@param ["add_last_generated_block", "remove_last_added_block"]
add_block_with_batch_number = 0 #@param {type:"slider", min:0, max:15, step:1}
render_MIDI_to_audio = False # @param {type:"boolean"}

print('=' * 70)

if block_action == 'add_last_generated_block':
  melody_chords_f.extend(out0[add_block_with_batch_number])
  print('Block added!')
else:
  melody_chords_f = melody_chords_f[:max(number_of_prime_tokens, (len(melody_chords_f)-384))]
  print('Block removed!')

print('=' * 70)
print('Composition now has', (len(melody_chords_f) // 4), 'notes')
print('Composition now has', len(melody_chords_f), 'tokens')


print('=' * 70)
print('Sample INTs', out1[:12])
print('=' * 70)

if len(melody_chords_f) != 0:

    song = melody_chords_f
    song_f = []
    tim = 0
    dur = 0
    vel = 0
    pitch = 0
    channel = 0

    son = []
    song1 = []

    for s in song:
      if s > 256 and s < (12*9)+640:
        son.append(s)
      else:
        if len(son) == 4:
          song1.append(son)
        son = []
        son.append(s)


    for ss in song1:

        if ss[0] < 128:
          tim += ss[0] * 8

        dur = (ss[1]-256) * 16

        if (ss[2]-384) > 128:
          pitch = (ss[2]-384) - 128
        else:
          pitch = (ss[2]-384)


        channel = (ss[3]-640) // 9
        vel = ((ss[3]-640) % 9) * 15

        song_f.append(['note', tim, dur, channel, pitch, vel ])

    detailed_stats = TMIDIX.Tegridy_ms_SONG_to_MIDI_Converter(song_f,
                                                              output_signature = 'Orchestrator',
                                                              output_file_name = '/content/Orchestrator-Music-Composition',
                                                              track_name='Project Los Angeles',
                                                              list_of_MIDI_patches=[0, 24, 32, 40, 42, 46, 56, 71, 73, 0, 53, 19, 0, 0, 0, 0])

    print('=' * 70)
    print('Displaying resulting composition...')
    print('=' * 70)

    fname = '/content/Orchestrator-Music-Composition'

    x = []
    y =[]
    c = []

    colors = ['red', 'yellow', 'green', 'cyan', 'blue', 'pink', 'orange', 'purple', 'gray', 'white', 'gold', 'silver']

    if block_action == 'add_last_generated_block':
      block_lines.append((song_f[-1][1] / 1000))

    else:
      if len(block_lines) > 1:
        block_lines.pop()

    for s in song_f:
      x.append(s[1] / 1000)
      y.append(s[4])
      c.append(colors[s[3]])

    if render_MIDI_to_audio:
      FluidSynth("/usr/share/sounds/sf2/FluidR3_GM.sf2", 16000).midi_to_audio(str(fname + '.mid'), str(fname + '.wav'))
      display(Audio(str(fname + '.wav'), rate=16000))

    plt.figure(figsize=(14,5))
    ax=plt.axes(title=fname)
    ax.set_facecolor('black')

    plt.scatter(x,y, c=c)

    for bl in block_lines:
      ax.axvline(x=bl, c='w')

    plt.xlabel("Time")
    plt.ylabel("Pitch")
    plt.show()

"""# Congrats! You did it! :)"""