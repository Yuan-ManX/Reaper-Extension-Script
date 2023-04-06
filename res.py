# Reaper Extension Script (RES)
import reaper_python as reaper
import os
import numpy as np


###################################################################
# 如何在Reaper中创建一个新的MIDI音轨，然后将一些MIDI事件添加到该轨道中。

# 创建新的MIDI音轨
track = reaper.CreateNewMIDIItemInProj(0, 0, 0, False)

# 获取轨道的MIDI编辑器
midi_editor = reaper.MIDIEditor_GetActive()

# 将MIDI编辑器聚焦到新创建的音轨
reaper.MIDIEditor_OnCommand(midi_editor, 40214)

# 获取MIDI编辑器的当前光标位置
ppq_pos = reaper.MIDI_GetPPQPosFromProjTime(track, 0)

# 添加一个MIDI CC事件
reaper.MIDI_InsertCC(track, False, False, ppq_pos, 0, 0, 0, 11, 127)

# 添加一个MIDI Note-On事件
reaper.MIDI_InsertNote(track, False, False, ppq_pos + 240, 0, 64, 127)

# 添加一个MIDI Note-Off事件
reaper.MIDI_InsertNote(track, False, False, ppq_pos + 480, 0, 64, 0)

# 更新MIDI编辑器显示
reaper.MIDIEditor_OnCommand(midi_editor, 40466)


###################################################################
# 如何从一个MIDI文件中读取所有音符，并将其转换为MIDI事件。

# 打开MIDI文件
midi_file = reaper.MIDIEditor_LastFocused_OnCommand(40452, False)

# 获取MIDI文件中的所有轨道
track_count = reaper.CountTrackMediaItems(0)

# 遍历所有轨道
for i in range(track_count):
    track = reaper.GetTrack(0, i)

    # 获取轨道中的所有MIDI音符
    midi_count = reaper.CountTrackMediaItems(track)
    for j in range(midi_count):
        midi_item = reaper.GetTrackMediaItem(track, j)
        take = reaper.GetActiveTake(midi_item)

        # 遍历所有MIDI音符并转换为MIDI事件
        midi_count = reaper.MIDI_CountEvts(take)
        for k in range(midi_count):
            midi_event = reaper.MIDI_GetEvt(take, k, None, None, None, None, None, None, None)
            if midi_event[0] == 9:  # Note-On事件
                pitch = midi_event[3]
                velocity = midi_event[4]
                ppq_pos = midi_event[1]
                reaper.MIDI_InsertNote(track, False, False, ppq_pos, 0, pitch, velocity)
            elif midi_event[0] == 8:  # Note-Off事件
                pitch = midi_event[3]
                velocity = 0
                ppq_pos = midi_event[1]
                reaper.MIDI_InsertNote(track, False, False, ppq_pos, 0, pitch, velocity)
            elif midi_event[0] == 11:  # CC事件
                cc_num = midi_event[3]
                cc_value = midi_event[4]
                ppq_pos = midi_event[1]
                reaper.MIDI_InsertCC(track, False, False, ppq_pos, 0, 0, 0, cc_num, cc_value)

# 关闭MIDI编辑器
reaper.MIDIEditor_OnCommand(midi_file, 40614)


###################################################################
# 如何读取一个音频文件、对其进行音量增益、并将其保存到新文件中。

# 获取当前工程的路径
project_path = reaper.EnumProjects(-1, "")
project_dir = os.path.dirname(project_path)

# 设置要处理的音频文件路径
audio_file_path = os.path.join(project_dir, "audio_file.wav")

# 获取音频文件的采样率和通道数
audio_samplerate, audio_channels = reaper.GetMediaFileSampleRate(reaper.EnumProjects(-1, ""), audio_file_path), reaper.GetMediaFileNumChannels(audio_file_path)

# 打开音频文件并读取数据
audio_file = reaper.PCM_Source_CreateFromFile(audio_file_path)
audio_length = reaper.GetMediaSourceLength(audio_file)
audio_samples = int(audio_length * audio_samplerate)
audio_buffer = reaper.new_array(audio_samples * audio_channels)
reaper.PCM_Source_GetSection(audio_file, 0, audio_length, audio_buffer, 0, audio_samples * audio_channels)

# 计算音频数据的最大值
max_val = 0
for i in range(audio_samples * audio_channels):
    val = abs(reaper.array_get(audio_buffer, i))
    if val > max_val:
        max_val = val

# 计算增益系数
gain = 1.0 / max_val

# 对音频数据应用增益
for i in range(audio_samples * audio_channels):
    new_val = reaper.array_get(audio_buffer, i) * gain
    reaper.array_set(audio_buffer, i, new_val)

# 创建新的音频文件并将增益应用到数据上
new_audio_file_path = os.path.join(project_dir, "audio_file_gain.wav")
reaper.PCM_Source_CreateFromType("WAV", new_audio_file_path)
new_audio_file = reaper.PCM_Source_CreateFromFile(new_audio_file_path)
reaper.PCM_Source_SetSampleRate(new_audio_file, audio_samplerate)
reaper.PCM_Source_SetNumChannels(new_audio_file, audio_channels)
reaper.PCM_Source_SetLength(new_audio_file, audio_length, True)
reaper.PCM_Source_Write(new_audio_file, audio_buffer, audio_samples * audio_channels, 1.0)

# 清除内存
reaper.PCM_Source_Destroy(audio_file)
reaper.PCM_Source_Destroy(new_audio_file)
reaper.delete_array(audio_buffer)


###################################################################
# 如何将多个音频文件混合成一个新的音频文件，并对混合后的音频数据应用音量增益。

# 获取当前工程的路径
project_path = reaper.EnumProjects(-1, "")
project_dir = os.path.dirname(project_path)

# 设置要混合的音频文件路径列表
audio_file_paths = [os.path.join(project_dir, "audio_file1.wav"), os.path.join(project_dir, "audio_file2.wav")]

# 获取音频文件的采样率和通道数
audio_samplerate, audio_channels = reaper.GetMediaFileSampleRate(reaper.EnumProjects(-1, ""), audio_file_paths[0]), reaper.GetMediaFileNumChannels(audio_file_paths[0])

# 打开音频文件并读取数据
audio_buffers = []
for audio_file_path in audio_file_paths:
    audio_file = reaper.PCM_Source_CreateFromFile(audio_file_path)
    audio_length = reaper.GetMediaSourceLength(audio_file)
    audio_samples = int(audio_length * audio_samplerate)
    audio_buffer = reaper.new_array(audio_samples * audio_channels)
    reaper.PCM_Source_GetSection(audio_file, 0, audio_length, audio_buffer, 0, audio_samples * audio_channels)
    audio_buffers.append(audio_buffer)
    reaper.PCM_Source_Destroy(audio_file)

# 计算音频数据的最大值
max_val = 0
for audio_buffer in audio_buffers:
    for i in range(audio_samples * audio_channels):
        val = abs(reaper.array_get(audio_buffer, i))
        if val > max_val:
            max_val = val

# 计算增益系数
gain = 1.0 / max_val

# 对音频数据应用增益并混合
mixed_audio_buffer = reaper.new_array(audio_samples * audio_channels)
for audio_buffer in audio_buffers:
    for i in range(audio_samples * audio_channels):
        new_val = reaper.array_get(audio_buffer, i) * gain
        mixed_audio_buffer[i] += new_val

# 创建新的音频文件并将混合后的音频数据写入
new_audio_file_path = os.path.join(project_dir, "mixed_audio_file.wav")
reaper.PCM_Source_CreateFromType("WAV", new_audio_file_path)
new_audio_file = reaper.PCM_Source_CreateFromFile(new_audio_file_path)
reaper.PCM_Source_SetSampleRate(new_audio_file, audio_samplerate)
reaper.PCM_Source_SetNumChannels(new_audio_file, audio_channels)
reaper.PCM_Source_SetLength(new_audio_file, audio_length, True)
reaper.PCM_Source_Write(new_audio_file, mixed_audio_buffer, audio_samples * audio_channels, 1.0)

# 清除内存
reaper.PCM_Source_Destroy(new_audio_file)
reaper.delete_array(mixed_audio_buffer)
for audio_buffer in audio_buffers:
    reaper.delete_array(audio_buffer)


###################################################################
# 使用Python和Reaper API处理音频数据

# 获取当前工程的采样率和每个采样点的位数
srate = reaper.SNM_GetDoubleConfigVar("projrate", 0.0)
nBits = reaper.SNM_GetIntConfigVar("projsnsformat", 0)

# 获取第一个音频轨道
track = reaper.GetTrack(0, 0)

# 获取该轨道的所有音频项目
item_count = reaper.CountTrackMediaItems(track)
audio_items = []
for i in range(item_count):
    item = reaper.GetTrackMediaItem(track, i)
    take = reaper.GetMediaItemTake(item, 0)
    if reaper.TakeIsMIDI(take):
        continue
    audio_items.append(item)

# 获取第一个音频项目的PCM数据
item = audio_items[0]
take = reaper.GetMediaItemTake(item, 0)
source = reaper.GetMediaItemTake_Source(take)
num_channels = reaper.GetMediaSourceNumChannels(source)

# 计算音频数据长度（单位：采样点）
item_len_samples = int(reaper.GetMediaItemInfo_Value(item, "D_LENGTH") * srate)
# 创建一个numpy数组来存储PCM数据
data = np.zeros((num_channels, item_len_samples), dtype=np.float32)

# 读取PCM数据并存储到numpy数组中
reaperPCM = reaper.new_array(item_len_samples * num_channels)
reaper.SNM_GetAudioAccessorSamples(
    source,  # 获取音频数据的源
    0,  # 起始位置（单位：采样点）
    item_len_samples,  # 结束位置（单位：采样点）
    reaperPCM  # 存储PCM数据的数组
)
for ch in range(num_channels):
    data[ch] = reaper.array_frompointer(reaperPCM, ch * item_len_samples)

# 在这里可以对音频数据进行处理，比如应用一个滤波器

# 将处理后的数据写回到Reaper中
for i, item in enumerate(audio_items):
    take = reaper.GetMediaItemTake(item, 0)
    source = reaper.GetMediaItemTake_Source(take)
    reaperPCM = reaper.new_array(item_len_samples * num_channels)
    for ch in range(num_channels):
        reaper.array_topointer(reaperPCM, ch * item_len_samples)[
            :item_len_samples
        ] = data[ch]
    reaper.SNM_AddAudioAccessorSamples(
        source,  # 写回的音频数据源
        0,  # 起始位置（单位：采样点）
        item_len_samples,  # 结束位置（单位：采样点）
        reaperPCM  # 包含要写入的PCM数据的数组
    )
    reaper.delete_array(reaperPCM)


###################################################################
# 使用Python访问和控制Reaper插件

# 获取选中的Track数量
selected_track_count = reaper.CountSelectedTracks(0)

# 在控制台打印选中的Track数量
print("选中的Track数量：", selected_track_count)

# 获取第一个选中的Track对象
selected_track = reaper.GetSelectedTrack(0, 0)

# 获取Track名称
track_name = reaper.GetTrackName(selected_track)

# 在控制台打印Track名称
print("选中的Track名称：", track_name)

# 获取Track上的第一个FX插件对象
fx = reaper.TrackFX_GetFX(selected_track, 0)

# 获取FX插件的名称
fx_name = reaper.TrackFX_GetFXName(selected_track, 0, "")

# 在控制台打印FX插件的名称
print("Track上的第一个FX插件名称：", fx_name)

# 获取FX插件参数数量
parameter_count = reaper.TrackFX_GetNumParams(selected_track, 0)

# 在控制台打印FX插件参数数量
print("FX插件参数数量：", parameter_count)

# 获取FX插件第一个参数的值
parameter_value = reaper.TrackFX_GetParam(selected_track, 0, 0)

# 在控制台打印FX插件第一个参数的值
print("FX插件第一个参数的值：", parameter_value)

# 设置FX插件第一个参数的值
reaper.TrackFX_SetParam(selected_track, 0, 0, 0.5)

# 获取MIDI Editor句柄
midi_editor = reaper.MIDIEditor_GetActive()

# 获取MIDI Editor中所有的Note
note_count, _, _, _ = reaper.MIDI_CountEvts(midi_editor, 0, 0, 0)

# 在控制台打印MIDI Editor中Note数量
print("MIDI Editor中Note数量：", note_count)

# 获取第一个Note的位置
retval, _, _, _, _, _ = reaper.MIDI_GetNote(midi_editor, 0)

# 在控制台打印第一个Note的位置
print("第一个Note的位置：", retval)

# 将第一个Note的位置设置为0
reaper.MIDI_SetNote(midi_editor, 0, 0, 0, 0, 0, 0, 0, 0, 0)

# 获取当前项目的总时长
project_length = reaper.GetProjectLength()

# 在控制台打印当前项目的总时长
print("当前项目的总时长：", project_length)

# 获取当前项目的BPM
bpm = reaper.Master_GetTempo()

# 在控制台打印当前项目的BPM
print("当前项目的BPM：", bpm)

# 获取 track 对象
track = reaper.GetTrack(0, 0)

# 获取 track 名称
track_name = reaper.GetTrackName(track, "")

# 输出 track 名称
print("Track Name:", track_name)

# 设置 track 名称
reaper.SetTrackName(track, "New Track Name", True)

# 创建新的 track
new_track = reaper.InsertTrackAtIndex(0, True)

# 在新 track 上插入 MIDI item
midi_item = reaper.CreateNewMIDIItemInProj(new_track, 0, 10, False)

# 获取 MIDI item 的 take 对象
take = reaper.GetTake(midi_item, 0)

# 获取 MIDI 矩阵
midi_matrix = reaper.MIDI_GetAllEvts(take, "")

# 输出 MIDI 矩阵
print("MIDI Matrix:", midi_matrix)

# 在 MIDI 矩阵中添加新的 MIDI 事件
new_event = "9 40 7F 1000"
midi_matrix += new_event

# 将新的 MIDI 矩阵写回 take
reaper.MIDI_SetAllEvts(take, midi_matrix)

# 获取当前播放位置
play_pos = reaper.GetPlayPosition()

# 设置循环区域
loop_start = play_pos
loop_end = play_pos + 10
reaper.GetSet_LoopTimeRange(True, False, loop_start, loop_end, False)

# 播放循环
reaper.Main_OnCommand(1007, 0)
