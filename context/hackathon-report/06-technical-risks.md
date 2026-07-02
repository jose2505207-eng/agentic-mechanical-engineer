# Key Technical Risks

## R1: LLM → CadQuery parameter mapping produces invalid geometry
**Mitigation:** hard parameter bounds in templates; validation layer rejects out-of-range values before CAD executes

## R2: URDF inertia/mass errors make simulation meaningless
**Mitigation:** compute mass properties directly from CadQuery solids with assigned material densities

## R3: ROCm/vLLM environment friction on Day 1
**Mitigation:** fallback to a hosted API for development; move inference to MI300X once stable (AMD usage is a judging factor, so this is fallback only, not the plan)

## R4: Scope creep
**Mitigation:** feature freeze end of Day 5; the non-goals list (see 05-mvp-scope.md) is contractual between the two team members
