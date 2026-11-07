import React from "react";
import { Composition } from "remotion";
import { FPS, HEIGHT, WIDTH } from "./brand";
import { ReelComposition, calculateReelMetadata, reelPropsSchema } from "./engine/ReelComposition";
import { SetupCheck, calculateSetupMetadata } from "./SetupCheck";

export const RemotionRoot: React.FC = () => (
  <>
    {/* Every Reel renders through this one data-driven composition: --props='{"slug":"<slug>"}' */}
    <Composition
      id="Reel"
      component={ReelComposition}
      schema={reelPropsSchema}
      calculateMetadata={calculateReelMetadata}
      defaultProps={{ slug: "my-project", showSafeZones: false }}
      durationInFrames={300}
      fps={FPS}
      width={WIDTH}
      height={HEIGHT}
    />
    <Composition
      id="SetupCheck"
      component={SetupCheck}
      calculateMetadata={calculateSetupMetadata}
      defaultProps={{}}
      durationInFrames={240}
      fps={FPS}
      width={WIDTH}
      height={HEIGHT}
    />
  </>
);
