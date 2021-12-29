DELETE FROM Event_ID WHERE event_id IN
							(SELECT event_id FROM Event_ID WHERE event_id NOT IN (
																			SELECT event_id FROM Event
																			INTERSECT SELECT event_id FROM Event_Structure
																			INTERSECT SELECT event_id FROM Event_FCs
																			INTERSECT SELECT event_id FROM Event_Races)
							);