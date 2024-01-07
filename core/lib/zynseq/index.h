enum TRANSPORT_CLOCK
{
};

// ** Library management functions **

void (g_pMidiLearnCb)(void, uint8_t);
void init(char name);
bool isModified();
void enableDebug(bool bEnable);
bool load(const char filename);
void save(const char filename);
uint16_t getVerticalZoom();
void setVerticalZoom(uint16_t zoom);
uint16_t getHorizontalZoom();
void setHorizontalZoom(uint16_t zoom);

// ** Direct MIDI interface **

void playNote(uint8_t note, uint8_t velocity, uint8_t channel, uint32_t duration = 0);
void sendMidiStart();
void sendMidiStop();
void sendMidiContinue();
void sendMidiSongPos(uint16_t pos);
void sendMidiSong(uint32_t pos);
void sendMidiClock();
void sendMidiCommand(uint8_t status, uint8_t value1, uint8_t value2);
uint8_t getTallyChannel();
void setTallyChannel(uint8_t channel);
uint8_t getTriggerChannel();
void setTriggerChannel(uint8_t channel);
uint8_t getTriggerNote(uint8_t bank, uint8_t sequence);
void setTriggerNote(uint8_t bank, uint8_t sequence, uint8_t note);

// ** Pattern management functions - pattern events are quantized to steps **
//!@todo Current implementation selects a pattern then operates on it. API may be simpler to comprehend if patterns were acted on directly by passing the pattern index, e.g. clearPattern(index)

void enableMidiRecord(bool enable);
bool isMidiRecord();
uint32_t createPattern();
uint32_t getPatternsInTrack(uint8_t bank, uint8_t sequence, uint32_t track);
uint32_t getPattern(uint8_t bank, uint8_t sequence, uint32_t track, uint32_t position);
uint32_t getPatternAt(uint8_t bank, uint8_t sequence, uint32_t track, uint32_t position);
void selectPattern(uint32_t pattern);
uint32_t getPatternIndex();
uint32_t getSteps();
uint32_t getBeatsInPattern();
void setBeatsInPattern(uint32_t beats);
uint32_t getPatternLength(uint32_t pattern);
uint32_t getClocksPerStep();
uint32_t getStepsPerBeat();
void setStepsPerBeat(uint32_t steps);
bool addNote(uint32_t step, uint8_t note, uint8_t velocity, float duration);
void removeNote(uint32_t step, uint8_t note);
int32_t getNoteStart(uint32_t step, uint8_t note);
uint8_t getNoteVelocity(uint32_t step, uint8_t note);
void setNoteVelocity(uint32_t step, uint8_t note, uint8_t velocity);
uint8_t getStutterCount(uint32_t step, uint8_t note);
void setStutterCount(uint32_t step, uint8_t note, uint8_t count);
uint8_t getStutterDur(uint32_t step, uint8_t note);
void setStutterDur(uint32_t step, uint8_t note, uint8_t dur);
float getNoteDuration(uint32_t step, uint8_t note);
bool addProgramChange(uint32_t step, uint8_t program);
void removeProgramChange(uint32_t step, uint8_t program);
uint8_t getProgramChange(uint32_t step);
void transpose(int8_t value);
void changeVelocityAll(int value);
void changeDurationAll(float value);
void changeStutterCountAll(int value);
void changeStutterDurAll(int value);
void clear();
void copyPattern(uint32_t source, uint32_t destination);
void setInputRest(uint8_t note);
uint8_t getInputRest();
void setScale(uint32_t scale);
uint32_t getScale();
void setTonic(uint8_t tonic);
uint8_t getTonic();
void setPatternModified(Pattern pPattern, bool bModified = true);
bool isPatternModified();
uint8_t getRefNote();
void setRefNote(uint8_t note);
uint32_t getLastStep();
uint32_t getPatternPlayhead();

// ** Track management functions **

bool addPattern(uint8_t bank, uint8_t sequence, uint32_t track, uint32_t position, uint32_t pattern, bool force);
void removePattern(uint8_t bank, uint8_t sequence, uint32_t track, uint32_t position);
void cleanPatterns();
void toggleMute(uint8_t bank, uint8_t sequence, uint32_t track);
	@retval	bool True if muted
bool isMuted(uint8_t bank, uint8_t sequence, uint32_t track);
void setChannel(uint8_t bank, uint8_t sequence, uint32_t track, uint8_t channel);
uint8_t getChannel(uint8_t bank, uint8_t sequence, uint32_t track);
uint8_t getPlayMode(uint8_t bank, uint8_t sequence);
void setPlayMode(uint8_t bank, uint8_t sequence, uint8_t mode);
uint8_t getPlayState(uint8_t bank, uint8_t sequence);
	@retval bool True if sequence empty else false if any pattern in sequence has any events
bool isEmpty(uint8_t bank, uint8_t sequence);
void setPlayState(uint8_t bank, uint8_t sequence, uint8_t state);
void togglePlayState(uint8_t bank, uint8_t sequence);
uint32_t getTracksInSequence(uint8_t bank, uint8_t sequence);
void stop();
uint32_t getPlayPosition(uint8_t bank, uint8_t sequence);
void setPlayPosition(uint8_t bank, uint8_t sequence, uint32_t clock);
uint32_t getSequenceLength(uint8_t bank, uint8_t sequence);
void clearSequence(uint8_t bank, uint8_t sequence);
uint8_t getGroup(uint8_t bank, uint8_t sequence);
void setGroup(uint8_t bank, uint8_t sequence, uint8_t group);
bool hasSequenceChanged(uint8_t bank, uint8_t sequence);
uint32_t addTrackToSequence(uint8_t bank, uint8_t sequence, uint32_t track=-1);
void removeTrackFromSequence(uint8_t bank, uint8_t sequence, uint32_t track);
void addTempoEvent(uint8_t bank, uint8_t sequence, uint32_t tempo, uint16_t bar=1, uint16_t tick=0);
uint32_t getTempoAt(uint8_t bank, uint8_t sequence, uint16_t bar=1, uint16_t tick=0);
void addTimeSigEvent(uint8_t bank, uint8_t sequence, uint8_t beats, uint8_t type, uint16_t bar);
uint16_t getTimeSigAt(uint8_t bank, uint8_t sequence, uint16_t bar);
void enableMidiLearn(uint8_t bank, uint8_t sequence, void cb_object, void (cbfunc)(void, uint8_t));
uint8_t getMidiLearnBank();
uint8_t getMidiLearnSequence();
void setSequence(uint8_t bank, uint8_t sequence);
void setSequenceName(uint8_t bank, uint8_t sequence, const char name);
const char getSequenceName(uint8_t bank, uint8_t sequence);
bool moveSequence(uint8_t bank, uint8_t sequence, uint8_t position);
void insertSequence(uint8_t bank, uint8_t sequence);
void removeSequence(uint8_t bank, uint8_t sequence);
void updateSequenceInfo();

// ** Bank management functions **

void setSequencesInBank(uint8_t bank, uint8_t sequences);
uint32_t getSequencesInBank(uint32_t bank);
void clearBank(uint32_t bank);
void setTransportToStartOfBar();
void solo(uint8_t bank, uint8_t sequence, uint32_t track, bool solo);
bool isSolo(uint8_t bank, uint8_t sequence, uint32_t track);
void transportLocate(uint32_t frame);
uint32_t transportGetLocation(uint32_t bar, uint32_t beat, uint32_t tick);
bool transportRequestTimebase();
void transportReleaseTimebase();
void transportStart(const char client);
void transportStop(const char client);
void transportToggle(const char client);
uint8_t transportGetPlayStatus();
void setTempo(double tempo);
double getTempo();
void setBeatsPerBar(uint32_t beats);
uint32_t getBeatsPerBar();
void transportSetSyncTimeout(uint32_t timeout);
void enableMetronome(bool enable = true);
bool isMetronomeEnabled();
void setMetronomeVolume(float level);
float getMetronomeVolume();
uint8_t getClockSource();
void setClockSource(uint8_t source);
double getFramesPerClock(double dTempo);
