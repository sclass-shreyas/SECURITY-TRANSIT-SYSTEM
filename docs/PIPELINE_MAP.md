# Pipeline Maps

## High-Level System Architecture
```mermaid
flowchart TD
    Operator[Operator / Camera Environment] -->|Video Source| FrameCapture[Frame Capture]
    FrameCapture --> Detector[YOLO Detection]
    Detector --> Tracker[DeepSORT Tracking]
    Tracker --> ZoneManager[Zone / Dwell Logic]
    ZoneManager --> EventBuilder[Event Payload Builder]
    EventBuilder --> EventPublisher[HTTP Event Publisher]
    EventPublisher -->|POST /events| MockServer[Mock FastAPI Receiver]
    FrameCapture -->|Display Frame| OpenCV[OpenCV Visualization]
```

## Runtime Execution Pipeline
```mermaid
flowchart TD
    Camera[Camera Input] --> Capture[FrameCapture.read_frame]
    Capture --> Preprocess[Resize Frame]
    Preprocess --> Inference[Detector.detect]
    Inference --> Filter[Class + Confidence Filter]
    Filter --> Tracking[ObjectTracker.update]
    Tracking --> ZoneCheck[ZoneManager.get_zones_for_object]
    ZoneCheck --> Dwell[ZoneManager.update_dwell]
    Dwell --> Payload[build_event payload]
    Payload --> Publish[EventPublisher.publish]
    Publish --> API[POST http://localhost:8000/events]
    Payload --> Overlay[Draw bounding boxes + zones]
    Overlay --> Display[cv2.imshow]
```

## Module Dependency Graph
```mermaid
flowchart TD
    main --> capture
    main --> detector
    main --> tracker
    main --> zone_manager
    main --> event_publisher
    main --> config
    detector --> config
    tracker --> 
    zone_manager --> 
    event_publisher --> config
    capture --> 
```

## API Flow Diagram
```mermaid
flowchart TD
    DetectionPipeline[Detection Pipeline]
    DetectionPipeline -->|POST /events| MockServer[Mock API Receiver]
    MockServer -->|200 OK| DetectionPipeline
    subgraph Detection Pipeline
      Capture[FrameCapture] --> Detector[Detector]
      Detector --> Tracker[ObjectTracker]
      Tracker --> Zoning[ZoneManager]
      Zoning --> EventBuild[Event Payload Builder]
      EventBuild --> Publisher[EventPublisher]
    end
```
