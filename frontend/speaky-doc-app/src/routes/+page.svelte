<script>
	/** @typedef {{ transcript: string, patient_name: string, chief_complaint: string, assessment: string, saved_file?: string }} ProcessResponse */

	/** @type {File | null} */
	let selectedFile = null;
	/** @type {ProcessResponse | null} */
	let result = null;
	let errorMessage = '';
	let statusMessage = 'Ready';
	let isSubmitting = false;
	let isRecording = false;

	/** @type {HTMLInputElement | undefined} */
	let fileInput;
	/** @type {MediaRecorder | null} */
	let mediaRecorder = null;
	/** @type {Blob[]} */
	let recordingChunks = [];
	/** @type {MediaStream | null} */
	let currentStream = null;

	/** @param {File | null} file */
	function isWav(file) {
		if (!file) return false;
		const type = (file.type || '').toLowerCase();
		const name = (file.name || '').toLowerCase();
		return type === 'audio/wav' || type === 'audio/x-wav' || name.endsWith('.wav');
	}

	/** @param {Event} event */
	function onFileChange(event) {
		const input = /** @type {HTMLInputElement} */ (event.currentTarget);
		const [file] = input.files || [];
		selectedFile = null;
		errorMessage = '';
		result = null;

		if (!file) {
			statusMessage = 'Ready';
			return;
		}

		if (!isWav(file)) {
			errorMessage = 'Please select a .wav file.';
			statusMessage = 'Invalid file type';
			input.value = '';
			return;
		}

		selectedFile = file;
		statusMessage = `Selected ${file.name}`;
	}

	/**
	 * @param {File} file
	 * @param {string} sourceLabel
	 */
	async function submitFile(file, sourceLabel) {
		isSubmitting = true;
		errorMessage = '';
		result = null;
		statusMessage = `Uploading ${sourceLabel}...`;

		try {
			const formData = new FormData();
			formData.append('audio', file, file.name);

			const res = await fetch('http://localhost:8000/api/process', {
				method: 'POST',
				body: formData
			});

			const payload = await res.json();
			if (!res.ok) {
				throw new Error(payload.error || 'Upload failed');
			}

			result = payload;
			statusMessage = `${sourceLabel} processed successfully`;
		} catch (error) {
			errorMessage = error instanceof Error ? error.message : 'Unexpected error';
			statusMessage = 'Request failed';
		} finally {
			isSubmitting = false;
		}
	}

	async function uploadSelectedFile() {
		if (!selectedFile) {
			errorMessage = 'Choose a .wav file first.';
			return;
		}

		await submitFile(selectedFile, 'file');
	}

	/** @param {AudioBuffer} audioBuffer */
	function audioBufferToWav(audioBuffer) {
		const channels = audioBuffer.numberOfChannels;
		const sampleRate = audioBuffer.sampleRate;
		const length = audioBuffer.length;
		const bytesPerSample = 2;
		const blockAlign = channels * bytesPerSample;
		const dataSize = length * blockAlign;
		const buffer = new ArrayBuffer(44 + dataSize);
		const view = new DataView(buffer);
		let offset = 0;

		/** @param {string} value */
		function writeString(value) {
			for (let i = 0; i < value.length; i += 1) {
				view.setUint8(offset + i, value.charCodeAt(i));
			}
			offset += value.length;
		}

		/** @param {number} value */
		function writeUint32(value) {
			view.setUint32(offset, value, true);
			offset += 4;
		}

		/** @param {number} value */
		function writeUint16(value) {
			view.setUint16(offset, value, true);
			offset += 2;
		}

		writeString('RIFF');
		writeUint32(36 + dataSize);
		writeString('WAVE');
		writeString('fmt ');
		writeUint32(16);
		writeUint16(1);
		writeUint16(channels);
		writeUint32(sampleRate);
		writeUint32(sampleRate * blockAlign);
		writeUint16(blockAlign);
		writeUint16(16);
		writeString('data');
		writeUint32(dataSize);

		const channelData = [];
		for (let channel = 0; channel < channels; channel += 1) {
			channelData.push(audioBuffer.getChannelData(channel));
		}

		for (let sample = 0; sample < length; sample += 1) {
			for (let channel = 0; channel < channels; channel += 1) {
				const value = Math.max(-1, Math.min(1, channelData[channel][sample]));
				view.setInt16(offset, value < 0 ? value * 0x8000 : value * 0x7fff, true);
				offset += 2;
			}
		}

		return buffer;
	}

	/** @param {Blob} blob */
	async function convertBlobToWav(blob) {
		const arrayBuffer = await blob.arrayBuffer();
		const AudioContextCtor = window.AudioContext || /** @type {any} */ (window).webkitAudioContext;
		const audioContext = new AudioContextCtor();

		try {
			const decoded = await audioContext.decodeAudioData(arrayBuffer.slice(0));
			const wavBuffer = audioBufferToWav(decoded);
			return new Blob([wavBuffer], { type: 'audio/wav' });
		} finally {
			await audioContext.close();
		}
	}

	async function startRecording() {
		errorMessage = '';
		result = null;

		if (!navigator.mediaDevices?.getUserMedia) {
			errorMessage = 'Audio recording is not supported in this browser.';
			return;
		}

		try {
			currentStream = await navigator.mediaDevices.getUserMedia({ audio: true });
			recordingChunks = [];
			const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
				? 'audio/webm;codecs=opus'
				: 'audio/webm';

			mediaRecorder = new MediaRecorder(currentStream, { mimeType });
			mediaRecorder.ondataavailable = (event) => {
				if (event.data.size > 0) {
					recordingChunks.push(event.data);
				}
			};
			mediaRecorder.start();
			isRecording = true;
			statusMessage = 'Recording in progress...';
		} catch (error) {
			errorMessage = error instanceof Error ? error.message : 'Could not start recording';
			statusMessage = 'Recording failed';
		}
	}

	async function stopRecording() {
		if (!mediaRecorder || mediaRecorder.state === 'inactive') {
			return;
		}

		isRecording = false;
		statusMessage = 'Finalizing recording...';

		const stopPromise = new Promise((resolve) => {
			mediaRecorder?.addEventListener('stop', () => resolve(true), { once: true });
		});

		mediaRecorder.stop();
		await stopPromise;

		if (currentStream) {
			currentStream.getTracks().forEach((track) => track.stop());
			currentStream = null;
		}

		try {
			const rawBlob = new Blob(recordingChunks, { type: mediaRecorder.mimeType || 'audio/webm' });
			const wavBlob = await convertBlobToWav(rawBlob);
			const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
			const wavFile = new File([wavBlob], `recording-${timestamp}.wav`, { type: 'audio/wav' });
			selectedFile = wavFile;
			await submitFile(wavFile, 'recording');
		} catch (error) {
			errorMessage = error instanceof Error ? error.message : 'Recording conversion failed';
			statusMessage = 'Recording failed';
		}
	}
</script>

<svelte:head>
	<title>SpeakyDoc | Audio Intake</title>
</svelte:head>

<main class="page">
	<section class="hero">
		<p class="kicker">SpeakyDoc</p>
		<h1>Clinical Audio Intake</h1>
		<p class="subtitle">Upload a WAV file or record directly from the browser, then process it with the backend transcription pipeline.</p>
	</section>

	<section class="panel">
		<div class="control-row">
			<input
				bind:this={fileInput}
				type="file"
				accept=".wav,audio/wav,audio/x-wav"
				on:change={onFileChange}
				class="file-input"
			/>
			<button class="button" type="button" on:click={() => fileInput?.click()} disabled={isSubmitting || isRecording}>
				Select WAV
			</button>
			<button class="button primary" type="button" on:click={uploadSelectedFile} disabled={isSubmitting || !selectedFile || isRecording}>
				Upload File
			</button>
			<button class="button" type="button" on:click={startRecording} disabled={isSubmitting || isRecording}>
				Start Recording
			</button>
			<button class="button danger" type="button" on:click={stopRecording} disabled={!isRecording || isSubmitting}>
				Stop & Save WAV
			</button>
		</div>

		<div class="meta-row">
			<p>Status: {statusMessage}</p>
			{#if selectedFile}
				<p>Current file: {selectedFile.name}</p>
			{/if}
		</div>

		{#if errorMessage}
			<p class="error">{errorMessage}</p>
		{/if}
	</section>

	{#if result}
		<section class="panel result">
			<h2>Processing Result</h2>
			<pre>{JSON.stringify(result, null, 2)}</pre>
		</section>
	{/if}
</main>

<style>
	:global(body) {
		margin: 0;
		font-family: 'Helvetica Neue', 'Univers', 'Arial Narrow', Arial, sans-serif;
		background: linear-gradient(180deg, #f5f5f2 0%, #efefec 100%);
		color: #111;
	}

	.page {
		max-width: 980px;
		margin: 0 auto;
		padding: 3rem 1.25rem 4rem;
		display: grid;
		gap: 1.25rem;
	}

	.hero {
		padding-bottom: 1.5rem;
		border-bottom: 1px solid #c9c9c2;
	}

	.kicker {
		margin: 0;
		font-size: 0.75rem;
		letter-spacing: 0.24em;
		text-transform: uppercase;
		color: #5c5c57;
	}

	h1 {
		margin: 0.4rem 0 0;
		font-size: clamp(1.8rem, 4vw, 3rem);
		line-height: 1;
		letter-spacing: -0.02em;
		font-weight: 600;
	}

	.subtitle {
		max-width: 52rem;
		margin: 1rem 0 0;
		font-size: 1rem;
		line-height: 1.5;
		color: #333;
	}

	.panel {
		background: #f9f9f6;
		border: 1px solid #d0d0c9;
		padding: 1rem;
	}

	.control-row {
		display: flex;
		flex-wrap: wrap;
		gap: 0.6rem;
	}

	.file-input {
		display: none;
	}

	.button {
		border: 1px solid #111;
		background: transparent;
		color: #111;
		padding: 0.6rem 0.9rem;
		font-size: 0.85rem;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		cursor: pointer;
		transition: background-color 140ms ease, color 140ms ease, border-color 140ms ease;
	}

	.button:hover:enabled {
		background: #111;
		color: #fff;
	}

	.button.primary {
		background: #111;
		color: #fff;
	}

	.button.primary:hover:enabled {
		background: #2d2d2d;
	}

	.button.danger {
		border-color: #6d1111;
		color: #6d1111;
	}

	.button.danger:hover:enabled {
		background: #6d1111;
		color: #fff;
	}

	.button:disabled {
		opacity: 0.4;
		cursor: not-allowed;
	}

	.meta-row {
		margin-top: 0.8rem;
		display: flex;
		flex-wrap: wrap;
		gap: 1.2rem;
		font-size: 0.88rem;
		color: #3d3d39;
	}

	.error {
		margin: 0.8rem 0 0;
		font-size: 0.9rem;
		color: #8a1f1f;
	}

	.result h2 {
		margin: 0 0 0.7rem;
		font-size: 1rem;
		letter-spacing: 0.08em;
		text-transform: uppercase;
	}

	pre {
		margin: 0;
		padding: 0.8rem;
		border: 1px solid #d6d6d1;
		background: #f0f0eb;
		overflow: auto;
		font-family: 'SF Mono', Menlo, Consolas, monospace;
		font-size: 0.82rem;
		line-height: 1.45;
	}

	@media (max-width: 680px) {
		.page {
			padding-top: 2rem;
		}

		.control-row {
			flex-direction: column;
		}

		.button {
			width: 100%;
		}
	}
</style>
