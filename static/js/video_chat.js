let localStream;
let remoteStream;
let peerConnection;
let socket;
let roomId;
let isAudioEnabled = true;
let isVideoEnabled = true;

const iceServers = {
    iceServers: [
        { urls: 'stun:stun.l.google.com:19302' },
        { urls: 'stun:stun1.l.google.com:19302' }
    ]
};

async function initializeVideoChat(sessionRoomId) {
    roomId = sessionRoomId;
    socket = io();
    
    try {
        localStream = await navigator.mediaDevices.getUserMedia({
            video: true,
            audio: true
        });
        document.getElementById('local-video').srcObject = localStream;
        
        socket.emit('join', { roomId: roomId });
    } catch (err) {
        console.error('Error accessing media devices:', err);
        alert('Unable to access camera or microphone. Please check permissions.');
    }
    
    socket.on('user-connected', () => {
        createPeerConnection();
    });
    
    socket.on('user-disconnected', () => {
        if (peerConnection) {
            peerConnection.close();
        }
        document.getElementById('session-status').textContent = 'Disconnected';
    });
    
    socket.on('ice-candidate', async (candidate) => {
        if (peerConnection) {
            await peerConnection.addIceCandidate(new RTCIceCandidate(candidate));
        }
    });
    
    socket.on('offer', async (offer) => {
        if (!peerConnection) {
            createPeerConnection();
        }
        await peerConnection.setRemoteDescription(new RTCSessionDescription(offer));
        const answer = await peerConnection.createAnswer();
        await peerConnection.setLocalDescription(answer);
        socket.emit('answer', { roomId: roomId, answer: answer });
    });
    
    socket.on('answer', async (answer) => {
        await peerConnection.setRemoteDescription(new RTCSessionDescription(answer));
    });
}

function createPeerConnection() {
    peerConnection = new RTCPeerConnection(iceServers);
    
    localStream.getTracks().forEach(track => {
        peerConnection.addTrack(track, localStream);
    });
    
    peerConnection.ontrack = (event) => {
        document.getElementById('remote-video').srcObject = event.streams[0];
        document.getElementById('session-status').textContent = 'Connected';
    };
    
    peerConnection.onicecandidate = (event) => {
        if (event.candidate) {
            socket.emit('ice-candidate', {
                roomId: roomId,
                candidate: event.candidate
            });
        }
    };
    
    peerConnection.createOffer()
        .then(offer => peerConnection.setLocalDescription(offer))
        .then(() => {
            socket.emit('offer', {
                roomId: roomId,
                offer: peerConnection.localDescription
            });
        });
}

document.getElementById('toggle-video').addEventListener('click', () => {
    isVideoEnabled = !isVideoEnabled;
    localStream.getVideoTracks().forEach(track => {
        track.enabled = isVideoEnabled;
    });
    document.getElementById('toggle-video').classList.toggle('btn-outline-primary');
    document.getElementById('toggle-video').classList.toggle('btn-primary');
});

document.getElementById('toggle-audio').addEventListener('click', () => {
    isAudioEnabled = !isAudioEnabled;
    localStream.getAudioTracks().forEach(track => {
        track.enabled = isAudioEnabled;
    });
    document.getElementById('toggle-audio').classList.toggle('btn-outline-primary');
    document.getElementById('toggle-audio').classList.toggle('btn-primary');
});

document.getElementById('end-call').addEventListener('click', () => {
    if (confirm('Are you sure you want to end this session?')) {
        if (peerConnection) {
            peerConnection.close();
        }
        if (localStream) {
            localStream.getTracks().forEach(track => track.stop());
        }
        socket.emit('leave-room', { roomId: roomId });
        window.location.href = '/';
    }
});

// Start timer when session begins
let sessionDuration = 0;
setInterval(() => {
    sessionDuration++;
    const minutes = Math.floor(sessionDuration / 60);
    const seconds = sessionDuration % 60;
    document.getElementById('session-duration').textContent = 
        `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
}, 1000);
