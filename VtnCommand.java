/*
 * Copyright 2015-present Open Networking Foundation
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package org.onosproject.vtn.cli;

import org.apache.karaf.shell.commands.Command;
import org.apache.karaf.shell.commands.Option;
import org.onlab.osgi.DefaultServiceDirectory;
import org.onlab.osgi.ServiceDirectory;
import org.onlab.packet.MacAddress;
import org.onosproject.cli.AbstractShellCommand;
import org.onosproject.core.ApplicationId;
import org.onosproject.core.CoreService;
import org.onosproject.net.Device;
import org.onosproject.net.DeviceId;
import org.onosproject.net.device.DeviceService;
import org.onosproject.net.flow.DefaultFlowRule;
import org.onosproject.net.flow.DefaultTrafficSelector;
import org.onosproject.net.flow.DefaultTrafficTreatment;
import org.onosproject.net.flow.FlowRule;
import org.onosproject.net.flow.FlowRuleProgrammable;
import org.onosproject.net.flow.criteria.PiCriterion;
import org.onosproject.net.meter.Band;
import org.onosproject.net.meter.DefaultBand;
import org.onosproject.net.meter.DefaultMeter;
import org.onosproject.net.meter.Meter;
import org.onosproject.net.meter.MeterCellId;
import org.onosproject.net.meter.MeterOperation;
import org.onosproject.net.meter.MeterProgrammable;
import org.onosproject.net.pi.model.PiActionId;
import org.onosproject.net.pi.model.PiMatchFieldId;
import org.onosproject.net.pi.model.PiMeterId;
import org.onosproject.net.pi.model.PiTableId;
import org.onosproject.net.pi.runtime.PiAction;
import org.onosproject.net.pi.runtime.PiMatchKey;
import org.onosproject.net.pi.runtime.PiMeterCellId;
import org.onosproject.net.pi.runtime.PiTableAction;
import org.onosproject.net.pi.runtime.PiTableEntry;
import org.onosproject.net.pi.runtime.PiTernaryFieldMatch;

import java.util.ArrayList;
import java.util.Collection;

import static org.onlab.util.ImmutableByteSequence.copyFrom;
import static org.onlab.util.ImmutableByteSequence.ofOnes;

/**
 * Supports for updating the external gateway virtualPort.
 */
@Command(scope = "onos", name = "p4-meter",
        description = "Supports for setting the external port name.")
public class VtnCommand extends AbstractShellCommand {

    @Option(name = "-d", aliases = "--device", description = "external port name.", required = true,
            multiValued = false)
    String deviceId = "";

    @Option(name = "-p", aliases = "--port", description = "external port name.", required = true,
            multiValued = false)
    String index = "";

    @Option(name = "-i", aliases = "--ingress", description = "external port name.", required = true,
            multiValued = false)
    String ingressPort = "";

    @Option(name = "-de", aliases = "--dest", description = "external port name.", required = true,
            multiValued = false)
    String dest = "";

    @Option(name = "-sr", aliases = "--src", description = "external port name.", required = true,
            multiValued = false)
    String src = "";

    @Option(name = "-r", aliases = "--rate", description = "external port name.", required = true,
            multiValued = false)
    String rate = "";

    @Option(name = "-s", aliases = "--burst", description = "external port name.", required = true,
            multiValued = false)
    String burst = "";

    @Override
    protected void execute() {

        ServiceDirectory serviceDirectory = new DefaultServiceDirectory();
        DeviceService deviceService = serviceDirectory.get(DeviceService.class);
        CoreService coreService = serviceDirectory.get(CoreService.class);

        MeterProgrammable programmable;
        Device device = deviceService.getDevice(DeviceId.deviceId(deviceId));
        if (device.is(MeterProgrammable.class)) {
            programmable = device.as(MeterProgrammable.class);
        } else {
            log.error("Device {} is not meter programmable", deviceId);
            return;
        }

        try {
            Collection<Meter> meters = programmable.getMeters().get();
            log.info("The meter of device {}", meters);
        } catch (Exception e) {
            log.error("Exception occurred while get meters");
            return;
        }

        if (!ingressPort.isEmpty()) {
            PiTableEntry tableEntry = PiTableEntry.builder()
                    .forTable(PiTableId.of("table0_control.table0"))
                    .withMatchKey(PiMatchKey.builder()
                                          .addFieldMatch(new PiTernaryFieldMatch(
                                                  PiMatchFieldId.of("standard_metadata.ingress_port"),
                                                  copyFrom(Short.valueOf(ingressPort)), ofOnes(2)))
                                          .addFieldMatch(new PiTernaryFieldMatch(
                                                  PiMatchFieldId.of("hdr.ethernet.src_addr"),
                                                  copyFrom(MacAddress.valueOf(src).toBytes()), ofOnes(6)))
                                          .addFieldMatch(new PiTernaryFieldMatch(
                                                  PiMatchFieldId.of("hdr.ethernet.dst_addr"),
                                                  copyFrom(MacAddress.valueOf(dest).toBytes()), ofOnes(6)))
                                          .build())
                    .withTimeout(1000)
                    .withPriority(1000)
                    .withAction(PiAction.builder().withId(PiActionId.of("_drop")).build())
                    .withCookie(0xfff0323)
                    .build();

            MeterCellId entryCellId = PiMeterCellId.ofDirect(PiMeterId.of("table0_control.table0_meter"), tableEntry);

            Collection<Band> bands = new ArrayList<Band>();
            bands.add(DefaultBand.builder().ofType(Band.Type.NONE)
                              .withRate(Long.valueOf(rate))
                              .burstSize(Long.valueOf(burst))
                              .build());
            bands.add(DefaultBand.builder().ofType(Band.Type.NONE)
                              .withRate(Long.valueOf(rate) + 10)
                              .burstSize(Long.valueOf(burst) + 10)
                              .build());
            Meter meter = DefaultMeter.builder()
                    .withCellId(entryCellId)
                    .withBands(bands)
                    .forDevice(DeviceId.deviceId(deviceId))
                    .build();

            MeterOperation operation = new MeterOperation(meter, MeterOperation.Type.MODIFY);
            try {
                Boolean isSuccess = programmable.performMeterOperation(operation).get();
                log.info("configure meter {}", isSuccess);
            } catch (Exception e) {
                log.error("Exception occurred while configure meters");
                return;
            }

            FlowRuleProgrammable flowrule;
            if (device.is(FlowRuleProgrammable.class)) {
                flowrule = device.as(FlowRuleProgrammable.class);
            } else {
                log.error("Device {} is not flow rule programmable", deviceId);
                return;
            }
            Collection<FlowRule> rules = new ArrayList<FlowRule>();
            FlowRule rule = DefaultFlowRule.builder()
                    .withSelector(DefaultTrafficSelector.builder()
                                          .matchPi(PiCriterion.builder()
                                                           .matchExact(PiMatchFieldId
                                                                               .of("local_metadata.meter_tag"), 2)
                                                           .build()).build())
                    .withTreatment(DefaultTrafficTreatment.builder()
                                           .piTableAction(PiAction.builder().withId(PiActionId.of("_drop")).build())
                                           .build())
                    .forTable(PiTableId.of("table0_control.filter"))
                    .withPriority(1000)
                    .makePermanent()
                    .forDevice(DeviceId.deviceId(deviceId))
                    .fromApp(coreService.getAppId("org.onosproject.app.vtn"))
                    .build();
            rules.add(rule);
            flowrule.applyFlowRules(rules);

        } else {
            MeterCellId ingressCellId = PiMeterCellId.ofIndirect(PiMeterId.of("port_meters_ingress.ingress_port_meter"),
                                                                 Long.valueOf(index));
            MeterCellId ergressCellId = PiMeterCellId.ofIndirect(PiMeterId.of("port_meters_egress.egress_port_meter"),
                                                                 Long.valueOf(index));
            Collection<Band> bands = new ArrayList<Band>();
            bands.add(DefaultBand.builder().ofType(Band.Type.NONE)
                              .withRate(Long.valueOf(rate))
                              .burstSize(Long.valueOf(burst))
                              .build());
            bands.add(DefaultBand.builder().ofType(Band.Type.NONE)
                              .withRate(Long.valueOf(rate) + 10)
                              .burstSize(Long.valueOf(burst) + 10)
                              .build());
            Meter meter1 = DefaultMeter.builder()
                    .withCellId(ingressCellId)
                    .withBands(bands)
                    .forDevice(DeviceId.deviceId(deviceId))
                    .build();

            Meter meter2 = DefaultMeter.builder()
                    .withCellId(ergressCellId)
                    .withBands(bands)
                    .forDevice(DeviceId.deviceId(deviceId))
                    .build();

            MeterOperation operation = new MeterOperation(meter1, MeterOperation.Type.MODIFY);
            try {
                Boolean isSuccess = programmable.performMeterOperation(operation).get();
                log.info("configure meter {}", isSuccess);
            } catch (Exception e) {
                log.error("Exception occurred while configure meters");
                return;
            }

            MeterOperation operation2 = new MeterOperation(meter2, MeterOperation.Type.MODIFY);
            try {
                Boolean isSuccess = programmable.performMeterOperation(operation2).get();
                log.info("configure meter {}", isSuccess);
            } catch (Exception e) {
                log.error("Exception occurred while configure meters");
                return;
            }

            try {
                Collection<Meter> meters = programmable.getMeters().get();
                log.info("The meter of device {}", meters);
            } catch (Exception e) {
                log.error("Exception occurred while get meters");
                return;
            }
        }

    }
}
