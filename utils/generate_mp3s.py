from pydub import AudioSegment

BASE_AUDIO = AudioSegment.from_mp3("5_min_blank.mp3")

for i in range(0, 30):
    image_audio = BASE_AUDIO[:i*1000]
    out_f = open("{}_seconds.mp3".format(i), 'w+')
    image_audio.export(out_f, format="mp3")
