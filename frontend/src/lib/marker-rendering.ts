import type { Marker } from "./types";

export interface MarkerRenderingState {
  markers: Marker[];
  allMarkersCount: number;
}

export function buildMarkerRenderingState(input: {
  markers: Marker[];
  abnormalMarkers?: Marker[];
}): MarkerRenderingState {
  const markers = input.markers.length ? input.markers : (input.abnormalMarkers ?? []);

  return {
    markers,
    allMarkersCount: markers.length
  };
}
